"""
Live Connection Monitor for PwnSafe
Background thread that monitors Pwnagotchi connection status with debouncing.
"""

import threading
import time
import socket
import platform
import subprocess
import psutil
from enum import Enum, auto
from contextlib import closing


class ConnectionState(Enum):
    UNKNOWN = auto()
    CHECKING = auto()
    CONNECTED = auto()
    DISCONNECTED = auto()


def _find_iface_10():
    """Return (ifname, ip, mask) for a UP interface on 10.0.0.0/24, else (None, '', '')."""
    try:
        stats = psutil.net_if_stats()
        for ifname, addrs in psutil.net_if_addrs().items():
            st = stats.get(ifname)
            if not st or not st.isup:
                continue
            for a in addrs:
                fam = getattr(a.family, "name", str(a.family))
                if fam.endswith("AF_INET"):
                    ip = a.address or ""
                    mask = getattr(a, "netmask", "") or ""
                    if ip.startswith("10.0.0.") and mask == "255.255.255.0":
                        return ifname, ip, mask
        return None, "", ""
    except Exception:
        return None, "", ""


def _tcp_connect(host: str, port: int, timeout: float = 0.8) -> bool:
    """Quick TCP connection check with proper cleanup."""
    try:
        with closing(socket.create_connection((host, port), timeout=timeout)):
            return True
    except Exception:
        return False


def _windows_icmp(host: str, timeout_ms: int = 700) -> bool:
    """Windows-specific ICMP ping with timeout."""
    try:
        if platform.system().lower() != "windows":
            return False
        p = subprocess.run(
            ["ping", "-n", "1", "-w", str(timeout_ms), host],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=(timeout_ms/1000.0 + 1.0),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return p.returncode == 0
    except Exception:
        return False


class ConnectionMonitor:
    """Background thread that monitors Pwnagotchi connection status."""
    
    def __init__(self, ui, interval_sec=2, host_ip="10.0.0.2", local_ip="10.0.0.1", debug=True):
        self.ui = ui
        self.interval = max(1, int(interval_sec))
        self.host_ip = host_ip
        self.local_ip = local_ip
        self.debug_monitor = debug  # Add debug flag
        self._stop = threading.Event()
        self._thr = None
        self._last_state = ConnectionState.UNKNOWN
        self._fail_streak = 0
        self._success_streak = 0
        self._last_seen_ok = 0.0  # Add watchdog timestamp
    
    def start(self):
        """Start the monitor thread."""
        if self._thr and self._thr.is_alive():
            return
        self._stop.clear()
        self._thr = threading.Thread(target=self._run, daemon=True)
        self._thr.start()
    
    def stop(self):
        """Stop the monitor thread."""
        self._stop.set()
    
    def set_interval(self, interval_sec):
        """Update monitor interval."""
        self.interval = max(1, int(interval_sec))
    
    def _run(self):
        """Main monitor loop with watchdog and proper state transitions."""
        while not self._stop.is_set():
            # Probe connection (fresh state every cycle)
            ok = self._probe()
            now = time.monotonic()
            
            # Update state with debouncing and watchdog
            if ok:
                self._last_seen_ok = now
                self._success_streak += 1
                self._fail_streak = 0
                if self._success_streak >= 1:
                    self._set_state_connected()
            else:
                self._fail_streak += 1
                self._success_streak = 0
                
                # Watchdog: force disconnect if we haven't seen OK for 3 intervals
                if self._last_seen_ok > 0 and (now - self._last_seen_ok) > (self.interval * 3):
                    self._fail_streak = max(self._fail_streak, 2)
                
                # Debounce: require 2 consecutive failures
                if self._fail_streak >= 2:
                    self._set_state_disconnected()
            
            # Sleep with small steps for responsive shutdown
            for _ in range(int(self.interval * 10)):
                if self._stop.is_set():
                    break
                time.sleep(0.1)
    
    def _probe(self) -> bool:
        """Layered connection check with fresh state every cycle."""
        try:
            # Step 1: Find UP interface on 10.0.0.0/24
            ifname, local_ip, mask = _find_iface_10()
            if not ifname:
                if self.debug_monitor and self._last_state != ConnectionState.DISCONNECTED:
                    if hasattr(self.ui, 'log_service'):
                        self.ui.log_service.log("No UP interface on 10.0.0.0/24", "WARNING")
                return False
            
            # Log interface success only on state change (verbose)
            if self.debug_monitor and self._last_state == ConnectionState.DISCONNECTED:
                if hasattr(self.ui, 'log_service'):
                    self.ui.log_service.log(f"IF ok: {ifname} ({local_ip})", "INFO", verbose=True)

            # Step 3: Try TCP:22 (works even when ICMP blocked) (verbose)
            host = self.host_ip
            if _tcp_connect(host, 22, timeout=0.8):
                if self.debug_monitor and self._last_state != ConnectionState.CONNECTED:
                    if hasattr(self.ui, 'log_service'):
                        self.ui.log_service.log(f"TCP:22 ok to {host}", "SUCCESS", verbose=True)
                return True

            # Step 4: Fallback to ICMP ping (verbose)
            if platform.system().lower() == "windows":
                if _windows_icmp(host, timeout_ms=700):
                    if self.debug_monitor and self._last_state != ConnectionState.CONNECTED:
                        if hasattr(self.ui, 'log_service'):
                            self.ui.log_service.log(f"ICMP ok to {host}", "SUCCESS", verbose=True)
                    return True
            else:
                if self._icmp_ping(host, timeout_ms=700):
                    if self.debug_monitor and self._last_state != ConnectionState.CONNECTED:
                        if hasattr(self.ui, 'log_service'):
                            self.ui.log_service.log(f"ICMP ok to {host}", "SUCCESS", verbose=True)
                    return True

            # Only show summary error when user-facing
            if self.debug_monitor and self._last_state == ConnectionState.CONNECTED:
                if hasattr(self.ui, 'log_service'):
                    self.ui.log_service.log("Unable to reach Pwnagotchi device", "ERROR")
            return False
            
        except Exception as e:
            # NEVER let exceptions escape
            if hasattr(self.ui, 'log_service'):
                self.ui.log_service.log(f"Probe error: {e}", "ERROR")
            return False
    
    
    def _icmp_ping(self, host, timeout_ms=700) -> bool:
        """ICMP ping check."""
        try:
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout_ms/1000)), host]
            result = subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=(
                    getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    if platform.system().lower() == "windows"
                    else 0
                ),
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _set_state_connected(self):
        """Set state to CONNECTED with logging on change."""
        if self._last_state != ConnectionState.CONNECTED:
            self._last_state = ConnectionState.CONNECTED
            if hasattr(self.ui, 'log_service'):
                self.ui.log_service.log("Pwnagotchi connected and ready!", "SUCCESS")
            if hasattr(self.ui, 'set_connection_state'):
                from ui_refactor import ConnState
                self.ui.set_connection_state(ConnState.CONNECTED, "Pwnagotchi Connected and Ready!")
    
    def _set_state_disconnected(self):
        """Set state to DISCONNECTED with logging on change."""
        if self._last_state != ConnectionState.DISCONNECTED:
            self._last_state = ConnectionState.DISCONNECTED
            if hasattr(self.ui, 'log_service'):
                self.ui.log_service.log("Pwnagotchi disconnected", "WARNING")
            if hasattr(self.ui, 'set_connection_state'):
                from ui_refactor import ConnState
                self.ui.set_connection_state(ConnState.ERROR, "Disconnected")
