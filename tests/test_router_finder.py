"""
test_router_finder.py
--------------------
Standalone test script to debug router finder functionality in the network automation web app.
Tests the ability to detect routers and interfaces for a given IP using RIB data.
"""

from routefind.router_finder import find_router_for_ip
from services.rib import get_rib_entries

def test_router_detection():
    """
    Test the router detection logic for a given IP address using RIB data.
    Prints relevant routes, processed interfaces, and the router found for the test IP.
    """
    # Test IP we're looking for
    test_ip = "192.168.100.2"
    # First get all routers from the database
    # We'll use router 192.168.1.1 as we know it has the interface
    router_ip = "192.168.1.1"
    print(f"\nTesting router detection for IP: {test_ip}")
    print("=" * 50)
    # Get routes directly from RIB
    print(f"\nGetting routes for router {router_ip}...")
    routes = get_rib_entries(router_ip)
    if not routes:
        print(f"No routes found for router {router_ip}")
        return
    print("\nRelevant Routes:")
    for route in routes:
        if '192.168.100' in route['destination']:
            print(f"\nDestination: {route['destination']}")
            print(f"Interface: {route['interface']}")
            print(f"Protocol: {route['protocol']}")
            print(f"Next Hop: {route['next_hop']}")
    # Build router info manually from routes
    interfaces = {}
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
            # If it's a /32 and directly connected, it's the interface IP
            if '/' in route['destination']:
                ip, prefix = route['destination'].split('/')
                if (prefix == '32' and 
                    route['next_hop'] and 'direct' in route['next_hop'].lower()):
                    interfaces[iface]['ip'] = ip.strip()
                elif prefix != '32':
                    interfaces[iface]['subnet'] = route['destination']
    print("\nProcessed Interfaces:")
    for iface, data in interfaces.items():
        print(f"\n{iface}:")
        print(f"  IP: {data['ip']}")
        print(f"  Subnet: {data['subnet']}")
    # Create router info dict
    router_info = {
        'name': f"Router_{router_ip}",
        'loopback': router_ip,
        'interfaces': interfaces,
        'routes': routes
    }
    # Create routers dict for find_router_for_ip
    routers = {router_ip: router_info}
    # Try to find router for the IP
    print("\nTrying to find router...")
    router_name, subnet = find_router_for_ip(test_ip, routers)
    if router_name:
        print(f"\nFound router: {router_name}")
        print(f"Subnet: {subnet}")
    else:
        print(f"\nCould not find router for IP: {test_ip}")

if __name__ == "__main__":
    test_router_detection() 