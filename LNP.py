# <Linux>

import os
import socket
import subprocess
import time
import threading
import netifaces
import psutil
import signal
from datetime import datetime
from termcolor import colored

v = "v1.0"
def print_ascii_art():
    ascii_art = """
    ██╗     ██╗███╗   ██╗██╗   ██╗██╗  ██╗    ███╗   ██╗███████╗████████╗
    ██║     ██║████╗  ██║██║   ██║╚██╗██╔╝    ████╗  ██║██╔════╝╚══██╔══╝
    ██║     ██║██╔██╗ ██║██║   ██║ ╚███╔╝     ██╔██╗ ██║█████╗     ██║   
    ██║     ██║██║╚██╗██║██║   ██║ ██╔██╗     ██║╚██╗██║██╔══╝     ██║   
    ███████╗██║██║ ╚████║╚██████╔╝██╔╝ ██╗    ██║ ╚████║███████╗   ██║   
    ╚══════╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═══╝╚══════╝   ╚═╝   
                    ██████╗ ██████╗  ██████╗ 
                    ██╔══██╗██╔══██╗██╔═══██╗
                    ██████╔╝██████╔╝██║   ██║
                    ██╔═══╝ ██╔══██╗██║   ██║
                    ██║     ██║  ██║╚██████╔╝
                    ╚═╝     ╚═╝  ╚═╝ ╚═════╝ 
    """
    print(colored(ascii_art, 'cyan'))
    print(colored("Created by: https://www.github.com/X2X0", 'yellow'))
    print(colored("Linux Network Diagnostics Tool {v}", 'green'))
    print(colored("-" * 70, 'white'))

def clear_screen():
    os.system('clear')

def get_interfaces():
    return netifaces.interfaces()

def get_interface_details(interface):
    addrs = netifaces.ifaddresses(interface)
    try:
        ip_info = addrs[netifaces.AF_INET][0]
        return {
            'ip': ip_info.get('addr', 'N/A'),
            'netmask': ip_info.get('netmask', 'N/A'),
            'broadcast': ip_info.get('broadcast', 'N/A')
        }
    except (KeyError, IndexError):
        return {'ip': 'N/A', 'netmask': 'N/A', 'broadcast': 'N/A'}

def get_default_gateway():
    try:
        gws = netifaces.gateways()
        default = gws['default'][netifaces.AF_INET]
        return default[0]
    except (KeyError, IndexError):
        return "N/A"

def check_internet_connection():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def execute_command(command):
    try:
        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
        return output.decode('utf-8')
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode('utf-8')}"

def ping_host(host, count=4):
    command = f"ping -c {count} {host}"
    return execute_command(command)

def traceroute(host):
    command = f"traceroute -m 15 {host}"
    return execute_command(command)

def dns_lookup(domain):
    command = f"dig +short {domain}"
    return execute_command(command)

def tcp_dump(interface, packets=10):
    command = f"sudo tcpdump -i {interface} -c {packets} -n"
    return execute_command(command)

def check_open_ports(host, ports):
    results = {}
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        if result == 0:
            results[port] = colored("OPEN", 'green')
        else:
            results[port] = colored("CLOSED", 'red')
        sock.close()
    return results

def get_network_stats():
    net_io = psutil.net_io_counters(pernic=True)
    stats = {}
    for interface, data in net_io.items():
        stats[interface] = {
            'bytes_sent': data.bytes_sent,
            'bytes_recv': data.bytes_recv,
            'packets_sent': data.packets_sent,
            'packets_recv': data.packets_recv,
            'errin': data.errin,
            'errout': data.errout,
            'dropin': data.dropin,
            'dropout': data.dropout
        }
    return stats

def monitor_network_traffic(interface, duration=5):
    print(colored(f"Monitoring traffic on {interface} for {duration} seconds...", 'yellow'))
    start_stats = psutil.net_io_counters(pernic=True)[interface]
    time.sleep(duration)
    end_stats = psutil.net_io_counters(pernic=True)[interface]
    
    bytes_sent = end_stats.bytes_sent - start_stats.bytes_sent
    bytes_recv = end_stats.bytes_recv - start_stats.bytes_recv
    
    print(colored(f"Bytes sent: {bytes_sent/1024:.2f} KB", 'cyan'))
    print(colored(f"Bytes received: {bytes_recv/1024:.2f} KB", 'cyan'))
    print(colored(f"Total: {(bytes_sent + bytes_recv)/1024:.2f} KB", 'green'))

def continuous_monitor(interface, interval=1.0, stop_event=None):
    if stop_event is None:
        stop_event = threading.Event()
    
    prev_stats = psutil.net_io_counters(pernic=True)[interface]
    try:
        while not stop_event.is_set():
            time.sleep(interval)
            curr_stats = psutil.net_io_counters(pernic=True)[interface]
            
            bytes_sent = curr_stats.bytes_sent - prev_stats.bytes_sent
            bytes_recv = curr_stats.bytes_recv - prev_stats.bytes_recv
            
            print(f"\r{datetime.now().strftime('%H:%M:%S')} | "
                  f"↑ {bytes_sent/1024:.2f} KB/s | "
                  f"↓ {bytes_recv/1024:.2f} KB/s", end='')
            
            prev_stats = curr_stats
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def scan_network(subnet):
    print(colored(f"Scanning network {subnet}/24 for active hosts...", 'yellow'))
    active_hosts = []
    
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        response = os.system(f"ping -c 1 -W 1 {ip} > /dev/null 2>&1")
        
        if response == 0:
            try:
                hostname = socket.gethostbyaddr(ip)[0]
            except socket.herror:
                hostname = "Unknown"
            
            active_hosts.append((ip, hostname))
            print(colored(f"Found: {ip} ({hostname})", 'green'))
    
    return active_hosts

def signal_handler(sig, frame):
    print(colored("\n\nExiting program...", 'yellow'))
    os._exit(0)

def main_menu():
    signal.signal(signal.SIGINT, signal_handler)
    
    while True:
        clear_screen()
        print_ascii_art()
        
        print(colored("MAIN MENU", 'green'))
        print(colored("1. Network Interface Information", 'white'))
        print(colored("2. Connection Test (Ping, DNS, Internet)", 'white'))
        print(colored("3. Advanced Network Diagnostics", 'white'))
        print(colored("4. Network Traffic Monitoring", 'white'))
        print(colored("5. Network Scanning", 'white'))
        print(colored("6. Exit", 'white'))
        
        choice = input(colored("\nEnter your choice (1-6): ", 'yellow'))
        
        if choice == '1':
            interface_menu()
        elif choice == '2':
            connection_test_menu()
        elif choice == '3':
            advanced_diagnostics_menu()
        elif choice == '4':
            traffic_monitoring_menu()
        elif choice == '5':
            network_scanning_menu()
        elif choice == '6':
            print(colored("Exiting program...", 'yellow'))
            break
        else:
            print(colored("Invalid choice. Press Enter to continue...", 'red'))
            input()

def interface_menu():
    clear_screen()
    print_ascii_art()
    
    interfaces = get_interfaces()
    gateway = get_default_gateway()
    
    print(colored("NETWORK INTERFACES", 'green'))
    print(colored(f"Default Gateway: {gateway}", 'cyan'))
    print(colored("-" * 50, 'white'))
    
    for i, interface in enumerate(interfaces, 1):
        details = get_interface_details(interface)
        print(colored(f"{i}. {interface}", 'yellow'))
        print(colored(f"   IP Address: {details['ip']}", 'white'))
        print(colored(f"   Netmask: {details['netmask']}", 'white'))
        print(colored(f"   Broadcast: {details['broadcast']}", 'white'))
        print(colored("-" * 50, 'white'))
    
    input(colored("Press Enter to return to main menu...", 'yellow'))

def connection_test_menu():
    clear_screen()
    print_ascii_art()
    
    print(colored("CONNECTION TESTS", 'green'))
    
    internet = check_internet_connection()
    status = colored("ONLINE", 'green') if internet else colored("OFFLINE", 'red')
    print(colored(f"Internet Connection: {status}", 'white'))
    
    print(colored("\nTesting DNS Resolution:", 'yellow'))
    domains = ["google.com", "github.com", "cloudflare.com"]
    for domain in domains:
        result = dns_lookup(domain)
        print(colored(f"{domain}: {result}", 'white'))
    
    print(colored("\nPinging Google DNS (8.8.8.8):", 'yellow'))
    result = ping_host("8.8.8.8")
    print(colored(result, 'white'))
    
    input(colored("\nPress Enter to return to main menu...", 'yellow'))

def advanced_diagnostics_menu():
    clear_screen()
    print_ascii_art()
    
    print(colored("ADVANCED NETWORK DIAGNOSTICS", 'green'))
    print(colored("1. Traceroute to a host", 'white'))
    print(colored("2. DNS Lookup", 'white'))
    print(colored("3. Port Scan", 'white'))
    print(colored("4. TCP Dump", 'white'))
    print(colored("5. Return to Main Menu", 'white'))
    
    choice = input(colored("\nEnter your choice (1-5): ", 'yellow'))
    
    if choice == '1':
        host = input(colored("Enter host to traceroute: ", 'yellow'))
        print(colored("\nExecuting traceroute...", 'green'))
        result = traceroute(host)
        print(colored(result, 'white'))
    
    elif choice == '2':
        domain = input(colored("Enter domain for DNS lookup: ", 'yellow'))
        print(colored("\nExecuting DNS lookup...", 'green'))
        result = dns_lookup(domain)
        print(colored(result, 'white'))
    
    elif choice == '3':
        host = input(colored("Enter host to scan: ", 'yellow'))
        print(colored("\nScanning common ports...", 'green'))
        common_ports = [21, 22, 23, 25, 53, 80, 110, 123, 143, 443, 465, 587, 993, 995, 3306, 3389, 5900, 8080]
        results = check_open_ports(host, common_ports)
        
        for port, status in results.items():
            service = socket.getservbyport(port) if port in [21, 22, 23, 25, 53, 80, 110, 143, 443] else "Unknown"
            print(colored(f"Port {port} ({service}): {status}", 'white'))
    
    elif choice == '4':
        interfaces = get_interfaces()
        print(colored("\nAvailable interfaces:", 'green'))
        for i, interface in enumerate(interfaces, 1):
            print(colored(f"{i}. {interface}", 'white'))
        
        idx = int(input(colored("\nSelect interface number: ", 'yellow'))) - 1
        if 0 <= idx < len(interfaces):
            interface = interfaces[idx]
            print(colored(f"\nExecuting TCP dump on {interface}...", 'green'))
            result = tcp_dump(interface)
            print(colored(result, 'white'))
        else:
            print(colored("Invalid interface selection", 'red'))
    
    input(colored("\nPress Enter to return to main menu...", 'yellow'))

def traffic_monitoring_menu():
    clear_screen()
    print_ascii_art()
    
    print(colored("NETWORK TRAFFIC MONITORING", 'green'))
    print(colored("1. Quick Traffic Snapshot", 'white'))
    print(colored("2. Live Traffic Monitor", 'white'))
    print(colored("3. Network Statistics", 'white'))
    print(colored("4. Return to Main Menu", 'white'))
    
    choice = input(colored("\nEnter your choice (1-4): ", 'yellow'))
    
    interfaces = get_interfaces()
    
    if choice in ['1', '2', '3']:
        print(colored("\nAvailable interfaces:", 'green'))
        for i, interface in enumerate(interfaces, 1):
            print(colored(f"{i}. {interface}", 'white'))
        
        idx = int(input(colored("\nSelect interface number: ", 'yellow'))) - 1
        if 0 <= idx < len(interfaces):
            interface = interfaces[idx]
            
            if choice == '1':
                monitor_network_traffic(interface)
            
            elif choice == '2':
                print(colored("\nStarting live traffic monitor (press Ctrl+C to stop)...", 'green'))
                try:
                    continuous_monitor(interface)
                except KeyboardInterrupt:
                    print(colored("\nMonitoring stopped", 'yellow'))
            
            elif choice == '3':
                stats = get_network_stats()[interface]
                print(colored("\nNetwork Statistics:", 'green'))
                print(colored(f"Bytes Sent: {stats['bytes_sent']/1048576:.2f} MB", 'white'))
                print(colored(f"Bytes Received: {stats['bytes_recv']/1048576:.2f} MB", 'white'))
                print(colored(f"Packets Sent: {stats['packets_sent']}", 'white'))
                print(colored(f"Packets Received: {stats['packets_recv']}", 'white'))
                print(colored(f"Input Errors: {stats['errin']}", 'white'))
                print(colored(f"Output Errors: {stats['errout']}", 'white'))
                print(colored(f"Input Drops: {stats['dropin']}", 'white'))
                print(colored(f"Output Drops: {stats['dropout']}", 'white'))
        else:
            print(colored("Invalid interface selection", 'red'))
    
    input(colored("\nPress Enter to return to main menu...", 'yellow'))

def network_scanning_menu():
    clear_screen()
    print_ascii_art()
    
    print(colored("NETWORK SCANNING", 'green'))
    
    interfaces = get_interfaces()
    valid_interfaces = []
    
    for interface in interfaces:
        details = get_interface_details(interface)
        if details['ip'] != 'N/A':
            valid_interfaces.append((interface, details['ip']))
    
    print(colored("Available interfaces with IP addresses:", 'yellow'))
    for i, (interface, ip) in enumerate(valid_interfaces, 1):
        print(colored(f"{i}. {interface}: {ip}", 'white'))
    
    if valid_interfaces:
        idx = int(input(colored("\nSelect interface number for network scan: ", 'yellow'))) - 1
        if 0 <= idx < len(valid_interfaces):
            interface, ip = valid_interfaces[idx]
            subnet = '.'.join(ip.split('.')[:3])
            
            print(colored(f"\nScanning subnet {subnet}.0/24 for active hosts...", 'green'))
            print(colored("This may take a few minutes. Press Ctrl+C to stop.", 'yellow'))
            
            try:
                active_hosts = scan_network(subnet)
                
                print(colored(f"\nFound {len(active_hosts)} active hosts:", 'green'))
                for ip, hostname in active_hosts:
                    print(colored(f"{ip} - {hostname}", 'white'))
            except KeyboardInterrupt:
                print(colored("\nScan interrupted by user", 'red'))
        else:
            print(colored("Invalid selection", 'red'))
    else:
        print(colored("No interfaces with valid IP addresses found", 'red'))
    
    input(colored("\nPress Enter to return to main menu...", 'yellow'))

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(colored("\nProgram terminated by user", 'yellow'))
    except Exception as e:
        print(colored(f"\nAn error occurred: {str(e)}", 'red'))
