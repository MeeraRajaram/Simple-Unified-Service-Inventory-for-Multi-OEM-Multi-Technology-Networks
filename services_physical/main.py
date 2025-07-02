import ipaddress
from ncclient import manager
import subprocess
from prettytable import PrettyTable
import importlib
import xml.etree.ElementTree as ET


def validate_ip(ip_str):
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def check_ping(ip):
    try:
        print(f"\n🔄 Pinging {ip}...")
        result = subprocess.run(['ping', '-c', '2', '-W', '1', ip],
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              timeout=5)
        
        if result.returncode == 0:
            print(f"✅ Successfully pinged {ip}")
            return True
        print(f"❌ Could not ping {ip}")
        return False
    except Exception as e:
        print(f"❌ Ping failed: {str(e)}")
        return False

def detect_device_vendor(m):
    """Detect the network device vendor by inspecting capabilities"""
    try:
        capabilities = list(m.server_capabilities)
        for cap in capabilities:
            cap = cap.lower()
            if 'cisco' in cap or 'ios-xe' in cap:
                return 'cisco'
            elif 'juniper' in cap or 'junos' in cap:
                return 'juniper'
            elif 'arista' in cap:
                return 'arista'
        return 'unknown'
    except Exception as e:
        print(f"⚠️ Vendor detection failed: {str(e)}")
        return 'unknown'

def connect_to_device(ip, username, password, vendor):
    """Connect to device using vendor-specific parameters (returns live session)"""
    device_params_map = {
        'cisco': {'name': 'iosxe'},
        'juniper': {'name': 'junos'},
        'arista': {'name': 'default'},
        'unknown': {'name': 'default'}
    }

    device_params = device_params_map.get(vendor, {'name': 'default'})

    try:
        m = manager.connect(
            host=ip,
            port=830,
            username=username,
            password=password,
            hostkey_verify=False,
            device_params=device_params,
            timeout=20
        )
        return m  # Keep session open
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return None
    
def get_physical_inventory(m, vendor):
    """Get physical inventory based on vendor"""
    try:
        if vendor == 'cisco':
            module = importlib.import_module('cisco_router_physical')
        elif vendor == 'juniper':
            module = importlib.import_module('juniper_router_physical')
        elif vendor == 'arista':
            module = importlib.import_module('arista_router_physical')
        else:
            print("⚠️ Unknown vendor, using Cisco as default for physical inventory")
            module = importlib.import_module('cisco_router_physical')
        
        print("\n🖧 Physical Inventory:")
        inventory_table = module.get_physical_inventory(m)
        if inventory_table:
            print(inventory_table)
        else:
            print("No physical inventory information available")
            
    except ImportError as e:
        print(f"❌ Error importing physical inventory module: {str(e)}")
    except Exception as e:
        print(f"❌ Error during physical inventory collection: {str(e)}")


def main():
    print("\n🚀 Multi-Vendor Network Service Discovery Tool")
    print("-------------------------------------------")

    ip = input("Enter router IP: ").strip()
    username="admin".strip()
    password="sshadmin123".strip()
    # username = input("Username: ").strip()
    # password = input("Password: ").strip()

    if not validate_ip(ip):
        print("❌ Invalid IP address format")
        return

    if not check_ping(ip):
        return

    # First try with default parameters
    m = connect_to_device(ip, username, password, 'unknown')
    if not m:
        return

    try:
        # Detect vendor
        vendor = detect_device_vendor(m)
        m = connect_to_device(ip, username, password, vendor)
        print(f"\n📌 Device Vendor: {vendor.upper() if vendor != 'unknown' else 'Unknown (using standard models)'}")

        # Import vendor-specific module
        try:
            if vendor == 'cisco':
                module = importlib.import_module('cisco_router_service')
            elif vendor == 'juniper':
                module = importlib.import_module('juniper_router_service')
            elif vendor == 'arista':
                module = importlib.import_module('arista_router_service')
            else:
                print("⚠️ Unknown vendor, using generic discovery methods")
                module = importlib.import_module('generic_router')  # You should create this

            # Get device info
            device_info = module.get_device_info(m)
            print(f"\n📌 Device Details:")
            print(f"Hostname: {device_info['hostname']}")
            print(f"IP Address: {ip}")
            print(f"Loopback IP: {device_info['loopback']}")

            # Get capabilities
            print("\n🔍 Checking supported YANG models...")
            capabilities = list(m.server_capabilities)
            cisco_native_supported = any('Cisco-IOS-XE-native' in cap for cap in capabilities)
            juniper_supported = any('junos' in cap.lower() for cap in capabilities)
            arista_supported = any('arista' in cap.lower() for cap in capabilities)
            openconfig_supported = any('openconfig' in cap.lower() for cap in capabilities)

            print(f"Cisco Native Model: {'✅' if cisco_native_supported else '❌'}")
            print(f"Juniper Model: {'✅' if juniper_supported else '❌'}")
            print(f"Arista Model: {'✅' if arista_supported else '❌'}")
            print(f"OpenConfig Model: {'✅' if openconfig_supported else '❌'}")

            # Discover services
            print("\n🔍 Service Configurations:")
            module.discover_services(m)
            get_physical_inventory(m, vendor)

        except ImportError as e:
            print(f"❌ Error importing vendor module: {str(e)}")
        except Exception as e:
            print(f"❌ Error during discovery: {str(e)}")
        

    finally:
        m.close_session()

if __name__ == '__main__':
    main()
