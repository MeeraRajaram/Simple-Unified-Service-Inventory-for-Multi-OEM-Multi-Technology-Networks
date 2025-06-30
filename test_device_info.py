from services.vendor_host import get_device_info

# Replace with your actual device info
# (You can edit this list as needed)
devices = [
    {"host": "10.0.12.1", "port": 830, "username": "admin", "password": "sshadmin123"},
    {"host": "10.0.12.2", "port": 830, "username": "admin", "password": "sshadmin123"},
    {"host": "10.0.13.1", "port": 830, "username": "admin", "password": "sshadmin123"},
    {"host": "10.0.13.2", "port": 830, "username": "admin", "password": "sshadmin123"},
]

for dev in devices:
    print(f"Testing {dev['host']} ...")
    hostname, software_version, vendor, status = get_device_info(
        dev["host"], dev["port"], dev["username"], dev["password"]
    )
    print(f"  Hostname: {hostname}")
    print(f"  Software Version: {software_version}")
    print(f"  Vendor: {vendor}")
    print(f"  Status: {status}")
    print("-" * 40) 