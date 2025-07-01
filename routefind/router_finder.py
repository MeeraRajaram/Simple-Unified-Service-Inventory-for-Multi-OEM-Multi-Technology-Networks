"""
Module: router_finder.py
Purpose: Provides functions for finding routers based on IP addresses and managing router information.
Functions:
- find_router_for_ip: Locates router and interface for a given IP
- get_router_info: Gets detailed information about a router
"""

from services.rib import get_rib_entries
from services.vendor_host import get_device_info
from .router_lookup import find_router_for_ip

# Default NETCONF settings
NETCONF_PORT = 830
NETCONF_USERNAME = "admin"
NETCONF_PASSWORD = "admin"

def find_router_for_ip(ip, routers):
    """
    Find router and interface for a given IP address.
    Args:
        ip (str): IP address to search for
        routers (dict): Dictionary of router information
    Returns:
        tuple: (router_name, interface_subnet) or (None, None) if not found
    """
    for router, info in routers.items():
        if info['loopback'] == ip:
            return router, None
        for iface, iface_data in info['interfaces'].items():
            if iface_data['ip'] == ip:
                return router, iface_data['subnet']
    return None, None

def get_router_info(router_ip, port=NETCONF_PORT, username=NETCONF_USERNAME, password=NETCONF_PASSWORD):
    """
    Get detailed information about a router.
    Args:
        router_ip (str): Router's IP address
        port (int): NETCONF port (default: 830)
        username (str): NETCONF username (default: admin)
        password (str): NETCONF password (default: admin)
    Returns:
        dict: Router information including interfaces and routes
    """
    router_info = get_device_info(router_ip, port, username, password)
    if not router_info or router_info[0] == "Unknown":
        return None
        
    hostname, version, vendor, status = router_info
    routes = get_rib_entries(router_ip)
    
    # Build interface information from routes
    interfaces = {}
    
    # First pass: Find all interfaces and their subnets (non /32 routes)
    for route in routes:
        if route['protocol'].lower() in ['connected', 'direct', 'local']:
            iface = route['interface']
            if not iface:
                continue
                
            if iface not in interfaces:
                interfaces[iface] = {
                    'ip': None,
                    'subnet': None
                }
            
            # If it's not a /32, it's the subnet for this interface
            if '/' in route['destination']:
                ip, prefix = route['destination'].split('/')
                if prefix != '32':
                    interfaces[iface]['subnet'] = route['destination']
    
    # Second pass: Find interface IPs (looking for /32 directly connected routes)
    for route in routes:
        if '/' in route['destination']:
            ip, prefix = route['destination'].split('/')
            if (prefix == '32' and 
                route['protocol'].lower() in ['connected', 'direct', 'local'] and
                route['next_hop'] and 'direct' in route['next_hop'].lower() and
                route['interface'] and route['interface'] in interfaces):
                
                # This is a directly connected /32 route - it's the interface IP
                iface = route['interface']
                interfaces[iface]['ip'] = ip.strip()
    
    return {
        'name': hostname or f"Router_{router_ip}",
        'loopback': router_ip,
        'vendor': vendor,
        'version': version,
        'status': status,
        'interfaces': interfaces,
        'routes': routes
    }

def find_source_and_dest_routers(source_ip, dest_ip):
    """
    Given source and destination IPs, return router/interface info for both.
    Returns: dict with 'source' and 'destination' keys, each mapping to the router info dict or None.
    """
    return {
        'source': find_router_for_ip(source_ip),
        'destination': find_router_for_ip(dest_ip)
    } 