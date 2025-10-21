#!/usr/bin/env python3
"""
Active Internet Connection Detector (Python Version)
This script identifies which network adapter is actively used for internet connectivity
"""

import subprocess
import socket
import json
import re
import sys
from typing import Dict, List, Optional, Tuple
import ipaddress

class NetworkDetector:
    def __init__(self):
        self.active_adapter = None
        self.adapters_info = {}
        
    def run_command(self, command: str) -> str:
        """Run a Windows command and return the output"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='ignore'  # Ignore encoding errors
            )
            if result.returncode != 0:
                print(f"Command '{command}' returned error code {result.returncode}")
                print(f"Error output: {result.stderr}")
            return result.stdout.strip()
        except Exception as e:
            print(f"Error running command '{command}': {e}")
            return ""

    def get_network_adapters(self) -> Dict:
        """Get all network adapters and their properties"""
        print("Gathering network adapter information...")
        
        adapters = {}
        
        # Method 1: Try using netsh interface show interface (more reliable)
        cmd = 'netsh interface show interface'
        output = self.run_command(cmd)
        
        print(f"Netsh output: {output[:200]}...")  # Debug output
        
        interface_lines = []
        for line in output.split('\n'):
            line = line.strip()
            if line and not line.startswith('-') and not line.startswith('Admin') and 'Loopback' not in line:
                # Parse the interface line
                # Format: Admin State    State      Type             Interface Name
                parts = line.split()
                if len(parts) >= 4:
                    admin_state = parts[0]
                    state = parts[1] 
                    interface_type = parts[2]
                    interface_name = ' '.join(parts[3:])
                    
                    if state.lower() in ['connected', 'disconnected'] and interface_name != 'Interface Name':
                        interface_lines.append({
                            'name': interface_name,
                            'state': state,
                            'admin_state': admin_state,
                            'type': interface_type
                        })
        
        print(f"Found {len(interface_lines)} interfaces from netsh")
        
        # Method 2: Get interface indices using ipconfig
        cmd = 'ipconfig /all'
        ipconfig_output = self.run_command(cmd)
        
        current_adapter = None
        adapter_info = {}
        
        for line in ipconfig_output.split('\n'):
            line = line.strip()
            
            # New adapter section
            if line and not line.startswith(' ') and ':' not in line.split('.')[0]:
                # This is likely an adapter name
                current_adapter = line.replace(':', '').strip()
                adapter_info[current_adapter] = {}
                
            elif current_adapter and ':' in line:
                # This is a property of the current adapter
                if 'IPv4 Address' in line:
                    ip = line.split(':')[-1].strip().replace('(Preferred)', '').strip()
                    adapter_info[current_adapter]['ip_address'] = ip
                elif 'Default Gateway' in line:
                    gateway = line.split(':')[-1].strip()
                    if gateway and gateway != '':
                        adapter_info[current_adapter]['default_gateway'] = gateway
                elif 'DHCP Enabled' in line:
                    adapter_info[current_adapter]['dhcp_enabled'] = 'Yes' in line
        
        # Combine information
        index = 1
        for iface in interface_lines:
            # Try to match with ipconfig info
            matched_info = {}
            for adapter_name, info in adapter_info.items():
                if any(part.lower() in adapter_name.lower() for part in iface['name'].lower().split()):
                    matched_info = info
                    break
            
            adapters[index] = {
                'name': iface['name'],
                'adapter_type': iface['type'],
                'speed': 'Unknown',
                'status': 'Connected' if iface['state'].lower() == 'connected' else 'Disconnected',
                'interface_index': index,
                'admin_state': iface['admin_state'],
                **matched_info
            }
            index += 1
        
        print(f"Final adapter count: {len(adapters)}")
        return adapters

    def get_connection_status(self, status_code: str) -> str:
        """Convert Windows connection status code to readable string"""
        status_map = {
            '0': 'Disconnected',
            '1': 'Connecting',
            '2': 'Connected',
            '3': 'Disconnecting',
            '4': 'Hardware not present',
            '5': 'Hardware disabled',
            '6': 'Hardware malfunction',
            '7': 'Media disconnected'
        }
        return status_map.get(status_code, 'Unknown')

    def get_ip_config(self, interface_name: str) -> Dict:
        """Get IP configuration for a specific interface by name"""
        config = {
            'ip_address': None,
            'subnet_mask': None,
            'default_gateway': None,
            'dns_servers': [],
            'dhcp_enabled': False
        }
        
        # Get IP address and subnet using netsh
        cmd = f'netsh interface ip show addresses "{interface_name}"'
        output = self.run_command(cmd)
        
        for line in output.split('\n'):
            line = line.strip()
            if 'IP Address:' in line:
                config['ip_address'] = line.split(':')[-1].strip()
            elif 'Subnet Prefix:' in line:
                prefix = line.split(':')[-1].strip().split('/')[-1]
                if prefix.isdigit():
                    try:
                        # Convert CIDR to subnet mask
                        config['subnet_mask'] = str(ipaddress.IPv4Network(f'0.0.0.0/{prefix}', strict=False).netmask)
                    except:
                        config['subnet_mask'] = f"/{prefix}"
            elif 'Default Gateway:' in line:
                gateway = line.split(':')[-1].strip()
                if gateway and gateway != 'none':
                    config['default_gateway'] = gateway
            elif 'DHCP enabled:' in line:
                config['dhcp_enabled'] = 'Yes' in line
        
        # Get DNS servers
        cmd = f'netsh interface ip show dns "{interface_name}"'
        output = self.run_command(cmd)
        
        for line in output.split('\n'):
            if 'DNS servers configured through DHCP:' in line or 'Statically Configured DNS Servers:' in line:
                continue
            elif line.strip() and re.match(r'^\s*\d+\.\d+\.\d+\.\d+', line):
                dns = line.strip()
                if dns not in config['dns_servers']:
                    config['dns_servers'].append(dns)
        
        return config

    def get_interface_name(self, interface_index: int) -> str:
        """Get interface name by index"""
        cmd = f'netsh interface show interface'
        output = self.run_command(cmd)
        
        for line in output.split('\n'):
            if str(interface_index) in line and 'Connected' in line:
                parts = line.split()
                if len(parts) >= 4:
                    return ' '.join(parts[3:])
        return f"Interface_{interface_index}"

    def get_default_routes(self) -> List[Dict]:
        """Get default routes (0.0.0.0/0)"""
        cmd = 'route print 0.0.0.0'
        output = self.run_command(cmd)
        
        routes = []
        parsing_routes = False
        
        for line in output.split('\n'):
            if 'Network Destination' in line and 'Netmask' in line:
                parsing_routes = True
                continue
            elif parsing_routes and line.strip():
                if line.startswith('=') or not line.strip():
                    break
                    
                parts = line.split()
                if len(parts) >= 5 and parts[0] == '0.0.0.0' and parts[1] == '0.0.0.0':
                    try:
                        routes.append({
                            'destination': parts[0],
                            'netmask': parts[1],
                            'gateway': parts[2],
                            'interface': parts[3],
                            'metric': int(parts[4]) if parts[4].isdigit() else 999
                        })
                    except (IndexError, ValueError):
                        continue
        
        # Sort by metric (lower is better)
        return sorted(routes, key=lambda x: x['metric'])

    def test_internet_connectivity(self, interface_ip: str = None) -> bool:
        """Test internet connectivity"""
        try:
            # Try to connect to Google's DNS
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            
            if interface_ip:
                try:
                    sock.bind((interface_ip, 0))
                except:
                    pass  # If binding fails, try without binding
            
            result = sock.connect_ex(('8.8.8.8', 53))
            sock.close()
            return result == 0
        except Exception:
            return False

    def find_active_connection(self) -> Optional[Dict]:
        """Find the active internet connection"""
        print("\n=== Active Internet Connection Detector ===")
        print("")
        
        # Get all adapters
        self.adapters_info = self.get_network_adapters()
        
        if not self.adapters_info:
            print("No network adapters found!")
            # Try a simpler approach
            print("Attempting alternative detection method...")
            return self.simple_detection_fallback()
        
        # Test each connected adapter for internet connectivity
        print("Testing network adapters for internet connectivity...")
        
        for idx, adapter in self.adapters_info.items():
            if adapter['status'] == 'Connected':
                print(f"Testing adapter: {adapter['name']}...")
                
                # Get additional IP config if not already present
                if not adapter.get('ip_address'):
                    ip_config = self.get_ip_config(adapter['name'])
                    adapter.update(ip_config)
                
                # Test internet connectivity
                if adapter.get('ip_address') and self.test_internet_connectivity(adapter['ip_address']):
                    print(f"  ✓ Internet access confirmed!")
                    self.active_adapter = adapter
                    return adapter
                else:
                    print(f"  ✗ No internet access or no IP address")
        
        print("No adapter with working internet connection found using primary method!")
        print("Trying fallback detection...")
        return self.simple_detection_fallback()

    def simple_detection_fallback(self) -> Optional[Dict]:
        """Simple fallback method using basic commands"""
        print("Using fallback detection method...")
        
        # Get default route
        routes = self.get_default_routes()
        if not routes:
            print("No default routes found!")
            return None
        
        best_route = routes[0]  # Lowest metric route
        print(f"Found default route via {best_route['gateway']} on interface {best_route['interface']}")
        
        # Test connectivity
        if self.test_internet_connectivity():
            print("✓ Internet connectivity confirmed!")
            
            # Create a basic adapter info
            fallback_adapter = {
                'name': f"Interface {best_route['interface']}",
                'adapter_type': 'Unknown',
                'speed': 'Unknown', 
                'status': 'Connected',
                'interface_index': 1,
                'ip_address': best_route['interface'],
                'default_gateway': best_route['gateway'],
                'route_info': best_route
            }
            
            self.active_adapter = fallback_adapter
            return fallback_adapter
        
        return None

    def display_connection_details(self):
        """Display detailed information about the active connection"""
        if not self.active_adapter:
            print("No active internet connection found!")
            return
        
        adapter = self.active_adapter
        print("\nActive Internet Connection Details:")
        print("===================================")
        print("")
        
        print("Network Adapter:")
        print(f"  Name: {adapter['name']}")
        print(f"  Type: {adapter['adapter_type']}")
        print(f"  Status: {adapter['status']}")
        print(f"  Speed: {adapter['speed']}")
        print(f"  Interface Index: {adapter['interface_index']}")
        print("")
        
        print("IP Configuration:")
        if adapter.get('ip_address'):
            print(f"  IP Address: {adapter['ip_address']}")
        if adapter.get('subnet_mask'):
            print(f"  Subnet Mask: {adapter['subnet_mask']}")
        print(f"  DHCP Enabled: {adapter.get('dhcp_enabled', 'Unknown')}")
        print("")
        
        print("Gateway Information:")
        if adapter.get('default_gateway'):
            print(f"  Default Gateway: {adapter['default_gateway']}")
        if adapter.get('route_info'):
            print(f"  Route Metric: {adapter['route_info']['metric']}")
        print("")
        
        if adapter.get('dns_servers'):
            print("DNS Servers:")
            for dns in adapter['dns_servers']:
                print(f"  {dns}")
        print("")
        
        print("Testing Internet Connectivity...")
        print("  Internet connectivity: CONFIRMED (adapter was pre-tested)")
        print("")

    def display_all_adapters(self):
        """Display all network adapters"""
        print("All Network Adapters:")
        print("=====================")
        
        for idx, adapter in self.adapters_info.items():
            is_active = ""
            color_code = ""
            
            if (self.active_adapter and 
                adapter['interface_index'] == self.active_adapter['interface_index']):
                is_active = " [ACTIVE FOR INTERNET]"
                color_code = "\033[92m"  # Green
            elif adapter['status'] == 'Connected':
                color_code = "\033[97m"  # White
            else:
                color_code = "\033[90m"  # Gray
            
            print(f"{color_code}  {adapter['name']} - {adapter['status']}{is_active}\033[0m")
            print(f"\033[90m    {adapter['adapter_type']} (Index: {adapter['interface_index']})\033[0m")

def get_detailed_connection_info():
    """Get detailed TCP connection information"""
    print("\n=== Detailed Network Analysis ===")
    print("")
    
    try:
        cmd = 'netstat -n | findstr ESTABLISHED'
        output = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout
        
        local_ips = {}
        for line in output.split('\n'):
            if line.strip() and 'ESTABLISHED' in line:
                parts = line.split()
                if len(parts) >= 4:
                    local_addr = parts[1].split(':')[0]
                    remote_addr = parts[2].split(':')[0]
                    
                    if local_addr not in local_ips:
                        local_ips[local_addr] = {
                            'count': 0,
                            'remote_ips': set()
                        }
                    
                    local_ips[local_addr]['count'] += 1
                    local_ips[local_addr]['remote_ips'].add(remote_addr)
        
        print("Active TCP Connections by Local IP:")
        for local_ip, info in local_ips.items():
            print(f"  Local IP: {local_ip} - Active Connections: {info['count']}")
            
    except Exception as e:
        print(f"Error getting connection details: {e}")

def main():
    """Main function"""
    try:
        detector = NetworkDetector()
        
        # Find and display active connection
        active_connection = detector.find_active_connection()
        
        if active_connection:
            detector.display_connection_details()
            detector.display_all_adapters()
        else:
            print("Could not determine active internet connection.")
            print("\nAll available adapters:")
            detector.display_all_adapters()
        
        print("\nOptions:")
        print("  Run 'get_detailed_connection_info()' for more network details")
        print("")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()