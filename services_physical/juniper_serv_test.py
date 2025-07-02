import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import getpass
import argparse
from ncclient import manager
from services_physical.juniper_serv import discover_services

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', type=str, help='Juniper device IP/hostname')
    parser.add_argument('--username', type=str, help='Username')
    parser.add_argument('--password', type=str, help='Password')
    args = parser.parse_args()

    host = args.host or input("Juniper device IP/hostname: ").strip()
    username = args.username or input("Username: ").strip()
    password = args.password or getpass.getpass("Password: ")
    port = 830

    try:
        with manager.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            hostkey_verify=False,
            device_params={'name': 'junos'},
            timeout=30
        ) as m:
            print("\n--- Juniper Service Inventory ---\n")
            discover_services(m)
    except Exception as e:
        print(f"Connection or retrieval failed: {e}") 