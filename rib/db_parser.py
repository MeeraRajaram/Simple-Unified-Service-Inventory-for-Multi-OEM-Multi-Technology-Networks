import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../services')))
from db import router_db
from rib import cisco, juniper, arista, nokia, huawei

def parse_and_dispatch():
    routers = router_db.get_latest_routers()
    all_results = []
    for hostname, software_version, ip, vendor, username, password in routers:
        result = None
        if vendor.lower() == 'cisco':
            result = cisco.handle_routing_info(hostname, ip, username, password)
        elif vendor.lower() == 'juniper':
            result = juniper.handle_routing_info(hostname, ip, username, password)
        elif vendor.lower() == 'arista':
            result = arista.handle_routing_info(hostname, ip, username, password)
        elif vendor.lower() == 'nokia':
            result = nokia.handle_routing_info(hostname, ip, username, password)
        elif vendor.lower() == 'huawei':
            result = huawei.handle_routing_info(hostname, ip, username, password)
        else:
            print(f"Unknown vendor for {ip}: {vendor}")
        all_results.append(result)
    return all_results
