import sqlite3
import ipaddress
from rib.db_utils import rib_db_manage
from services.db import router_db

def is_valid_host_in_subnet(ip, subnet):
    try:
        net = ipaddress.ip_network(subnet, strict=False)
        ip_obj = ipaddress.ip_address(ip)
        return ip_obj in net and ip_obj != net.network_address and ip_obj != net.broadcast_address
    except Exception:
        return False

def find_router_for_ip(ip):
    entries = rib_db_manage.get_entries()
    routers = router_db.get_routers()
    search_prefixes = [f"{ip}/32", f"{ip}/30", f"{ip}/24"]
    candidates = []
    # Collect all direct matches
    for prefix in search_prefixes:
        for router, loopback_ip, protocol, destination, interface, next_hop in entries:
            if destination == prefix and protocol.lower() in ['connected', 'local'] and next_hop.lower() in ['direct', 'directly connected', 'local']:
                candidates.append({
                    'rib_router': router,
                    'loopback_ip': loopback_ip,
                    'protocol': protocol,
                    'destination': destination,
                    'interface': interface,
                    'next_hop': next_hop
                })
    # 1. Prefer exact loopback match (and always get vendor/name from inventory)
    for c in candidates:
        for hostname, software_version, router_ip, vendor, username, password in routers:
            if c['loopback_ip'] == router_ip:
                return {
                    'router': hostname,
                    'vendor': vendor,
                    'router_ip': router_ip,
                    'interface': c['interface']
                }
    # 2. Prefer vendor match (e.g., Arista for 10.0.x.x) with subnet check
    for router, loopback_ip, protocol, destination, interface, next_hop in entries:
        if protocol.lower() == 'connected' and next_hop.lower() == 'direct':
            try:
                net = ipaddress.ip_network(destination, strict=False)
                ip_obj = ipaddress.ip_address(ip)
                if ip_obj in net:
                    for hostname, software_version, router_ip, vendor, username, password in routers:
                        if vendor.lower() == 'arista' and router_ip == loopback_ip:
                            return {
                                'router': hostname,
                                'vendor': vendor,
                                'router_ip': router_ip,
                                'interface': interface
                            }
            except Exception:
                continue
    # 3. Fallback: first candidate, but get vendor/name from inventory if possible
    if candidates:
        c = candidates[0]
        for hostname, software_version, router_ip, vendor, username, password in routers:
            if c['loopback_ip'] == router_ip:
                return {
                    'router': hostname,
                    'vendor': vendor,
                    'router_ip': router_ip,
                    'interface': c['interface']
                }
        # If not found in inventory, fallback to RIB info
        return {
            'router': c['rib_router'],
            'vendor': 'Unknown',
            'router_ip': c['loopback_ip'],
            'interface': c['interface']
        }
    return None 