import subprocess
import os
import winreg
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')

# Predefined DNS servers (public and privacy-focused)
DNS_SERVERS = [
    # Global Public DNS Providers
    '1.1.1.1',     # Cloudflare DNS (Global)
    '1.0.0.1',     # Cloudflare DNS (Global)
    '8.8.8.8',     # Google DNS (Global)
    '8.8.4.4',     # Google DNS (Global)
    '9.9.9.9',     # Quad9 DNS (Global)
    '149.112.112.112',  # Quad9 DNS (Global)

    # North America
    '64.6.64.6',   # Verisign DNS (USA)
    '64.6.65.6',   # Verisign DNS (USA)
    '208.67.222.222',  # OpenDNS (USA)
    '208.67.220.220',  # OpenDNS (USA)
    '76.76.2.0',   # Alternate DNS (USA)
    '76.76.10.0',  # Alternate DNS (USA)

    # Europe
    '77.88.8.8',   # Yandex DNS (Russia)
    '77.88.8.1',   # Yandex DNS (Russia)
    '195.46.39.39',  # SafeDNS (Europe)
    '195.46.39.40',  # SafeDNS (Europe)
    '91.239.100.100',  # UncensoredDNS (Denmark)
    '89.233.43.71',   # UncensoredDNS (Denmark)

    # Asia
    '114.114.114.114',  # Baidu DNS (China)
    '114.114.115.115',  # Baidu DNS (China)
    '223.5.5.5',   # AliDNS (China)
    '223.6.6.6',   # AliDNS (China)
    '180.76.76.76',  # Baidu DNS Alternative (China)
    '119.29.29.29',  # DNSPod DNS (China)

    # Middle East
    '185.51.200.2',  # Clean Browsing (Israel)
    '185.228.168.9',  # Clean Browsing (Israel)

    # South America
    '200.221.11.101',  # NIC.BR DNS (Brazil)
    '200.221.11.100',  # NIC.BR DNS (Brazil)

    # Africa
    '196.10.69.130',  # TENET (South Africa)
    '196.10.69.131',  # TENET (South Africa)

    # Oceania
    '202.8.95.20',   # APNIC DNS (Australia)
    '202.8.95.21',   # APNIC DNS (Australia)

    # Additional Global Providers
    '4.2.2.1',     # Level 3 DNS
    '4.2.2.2',     # Level 3 DNS
    '8.26.56.26',  # Comodo Secure DNS
    '8.20.247.20', # Comodo Secure DNS
    '156.154.70.1',  # Neustar DNS
    '156.154.71.1',  # Neustar DNS
    '208.91.112.53',  # GreenTeamDNS
    '208.91.112.52',  # GreenTeamDNS
    '216.146.35.35',  # Dyn DNS
    '216.146.36.36',  # Dyn DNS
    '94.140.14.14',  # AdGuard DNS
    '94.140.15.15',  # AdGuard DNS
]

def get_network_interfaces():
    """Get all network interface names."""
    try:
        result = subprocess.run(['wmic', 'nic', 'get', 'name'], capture_output=True, text=True, timeout=10)
        interfaces = [line.strip() for line in result.stdout.split('\n') if line.strip() and 'Name' not in line]
        return interfaces
    except Exception as e:
        logging.error(f"Error getting network interfaces: {e}")
        return []

def change_dns_without_admin(dns_servers=DNS_SERVERS):
    """
    Change DNS settings for network interfaces without admin privileges.
    Uses Windows Registry modification for non-admin DNS change.
    """
    try:
        # Get network interfaces
        interfaces = get_network_interfaces()
        if not interfaces:
            logging.warning("No network interfaces found.")
            return False

        # Iterate through interfaces and modify DNS
        for interface in interfaces:
            try:
                # Open network adapter key
                key_path = r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_READ) as key:
                    # Enumerate subkeys (interface-specific keys)
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            full_subkey_path = f"{key_path}\\{subkey_name}"
                            
                            # Open specific interface key
                            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, full_subkey_path, 0, winreg.KEY_ALL_ACCESS) as interface_key:
                                # Set DNS servers
                                winreg.SetValueEx(interface_key, 'NameServer', 0, winreg.REG_SZ, ','.join(dns_servers))
                                logging.info(f"DNS set to {dns_servers} for interface {interface}")
                        except PermissionError:
                            logging.warning(f"Cannot modify interface {interface} - insufficient permissions")
                        except Exception as e:
                            logging.error(f"Error modifying interface {interface}: {e}")

            except Exception as e:
                logging.error(f"Error processing interface {interface}: {e}")

        # Flush DNS cache
        subprocess.run(['ipconfig', '/flushdns'], check=False, timeout=10)
        logging.info("DNS cache flushed successfully")

        return True

    except Exception as e:
        logging.error(f"DNS change failed: {e}")
        return False

def main():
    """Main function to change DNS settings."""
    if change_dns_without_admin():
        print("DNS settings updated successfully!")
    else:
        print("Failed to update DNS settings.")

if __name__ == '__main__':
    main()
