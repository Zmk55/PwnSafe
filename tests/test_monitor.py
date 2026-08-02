import os
import subprocess
import unittest
from unittest import mock

import monitor


class _LogService:
    def log(self, *args, **kwargs):
        pass


class _UI:
    log_service = _LogService()

    def __init__(self):
        self.states = []

    def set_connection_state(self, state, message):
        self.states.append((state, message))


class ConnectionMonitorTests(unittest.TestCase):
    @mock.patch("monitor.subprocess.run")
    @mock.patch("monitor._tcp_connect", return_value=True)
    @mock.patch(
        "monitor._find_iface_10",
        return_value=("Ethernet 2", "10.0.0.1", "255.255.255.0"),
    )
    def test_successful_tcp_probe_does_not_spawn_console_commands(
        self, _find_interface, _tcp_connect, run
    ):
        connection_monitor = monitor.ConnectionMonitor(_UI())

        self.assertTrue(connection_monitor._probe())
        run.assert_not_called()

    @unittest.skipUnless(os.name == "nt", "Windows-only subprocess flags")
    @mock.patch("monitor.platform.system", return_value="Windows")
    @mock.patch("monitor.subprocess.run")
    def test_windows_ping_is_hidden(self, run, _system):
        run.return_value = mock.Mock(returncode=0)

        self.assertTrue(monitor._windows_icmp("10.0.0.2"))
        self.assertEqual(
            run.call_args.kwargs["creationflags"], subprocess.CREATE_NO_WINDOW
        )

    def test_monitor_does_not_publish_transient_checking_state(self):
        ui = _UI()
        connection_monitor = monitor.ConnectionMonitor(ui)

        def successful_probe_then_stop():
            connection_monitor._stop.set()
            return True

        connection_monitor._probe = successful_probe_then_stop
        connection_monitor._run()

        self.assertEqual(len(ui.states), 1)
        self.assertEqual(ui.states[0][0].name, "CONNECTED")


if __name__ == "__main__":
    unittest.main()
