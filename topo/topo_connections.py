import sqlite3
import os
from collections import defaultdict

from tabulate import tabulate  # Optional: for debugging/printing

# Paths
RIB_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rib_db.sqlite3'))
DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'directconndb'))
PROTO_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protodb'))

def get_router_data_from_rib():
    conn = sqlite3.connect(RIB_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT router, loopback_ip, protocol, destination, interface, next_hop FROM rib")
    rows = cur.fetchall()
    conn.close()
    # Build routers dict keyed by loopback_ip
    routers = defaultdict(list)
    for row in rows:
        router, loopback_ip, protocol, destination, interface, next_hop = row
        routers[loopback_ip].append(list(row))
    # Assign generic names
    router_names = {lb: f"Router{i}" for i, lb in enumerate(sorted(routers.keys()), 1)}
    # Build named_routers dict
    named_routers = {}
    for loopback, routes in routers.items():
        updated_routes = []
        for route in routes:
            updated_route = route.copy()
            updated_route[0] = router_names[loopback]
            updated_routes.append(updated_route)
        named_routers[router_names[loopback]] = {
            'loopback': loopback,
            'routes': updated_routes
        }
    return named_routers

def extract_interface_info(router_data):
    interface_info = defaultdict(list)
    for router_name, data in router_data.items():
        for route in data['routes']:
            if route[2] in ['Connected', 'Local', 'Direct'] and '/' in route[3]:
                ip_with_prefix = route[3]
                ip = ip_with_prefix.split('/')[0]
                interface = route[4]
                # Skip network addresses and multicast
                if not ip.endswith('.0') and ip not in ['224.0.0.5', '0.0.0.0']:
                    network = '.'.join(ip.split('.')[:3])
                    interface_info[router_name].append({
                        'interface': interface,
                        'ip': ip,
                        'network': network,
                        'full_network': route[3]
                    })
    return interface_info

def find_direct_connections(interface_info):
    direct_links = []
    router_names = list(interface_info.keys())
    for i, src_router in enumerate(router_names):
        for src_interface in interface_info[src_router]:
            # Skip if source interface is loopback
            if 'loopback' in src_interface['interface'].lower() or 'lo' in src_interface['interface'].lower():
                continue
            for j in range(i+1, len(router_names)):
                dest_router = router_names[j]
                for dest_interface in interface_info[dest_router]:
                    if 'loopback' in dest_interface['interface'].lower() or 'lo' in dest_interface['interface'].lower():
                        continue
                    if src_interface['network'] == dest_interface['network']:
                        direct_links.append([
                            src_router,
                            src_interface['ip'],
                            src_interface['interface'],
                            dest_interface['interface'],
                            dest_interface['ip'],
                            dest_router
                        ])
                        direct_links.append([
                            dest_router,
                            dest_interface['ip'],
                            dest_interface['interface'],
                            src_interface['interface'],
                            src_interface['ip'],
                            src_router
                        ])
    return direct_links

def save_direct_connections(direct_links, db_path=DIRECTCONN_DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS direct_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_router TEXT,
            source_ip TEXT,
            source_interface TEXT,
            dest_interface TEXT,
            dest_ip TEXT,
            dest_router TEXT
        )
    ''')
    cur.execute('DELETE FROM direct_connections')
    for row in direct_links:
        cur.execute('INSERT INTO direct_connections (source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router) VALUES (?, ?, ?, ?, ?, ?)', row)
    conn.commit()
    conn.close()

def extract_routes_with_next_hop(router_data, interface_info):
    routes_with_next_hop = []
    for router_name, data in router_data.items():
        for route in data['routes']:
            if len(route) >= 6 and route[5] not in ['', 'N/A', 'Directly connected', 'Direct', 'Local']:
                dest = route[3]
                next_hop = route[5]
                protocol = route[2]
                # Find source interface for this next hop
                source_interface = "Unknown"
                for iface in interface_info[router_name]:
                    ip = iface['ip']
                    if next_hop.startswith(ip.split('.')[0] + '.' + ip.split('.')[1] + '.' + ip.split('.')[2] + '.'):
                        source_interface = iface['interface']
                        break
                # Find destination interface (if available in other routers)
                dest_interface = "Unknown"
                for other_router, other_ifaces in interface_info.items():
                    if other_router != router_name:
                        for iface in other_ifaces:
                            if dest.startswith(iface['ip']):
                                dest_interface = iface['interface']
                                break
                routes_with_next_hop.append([
                    router_name,
                    source_interface,
                    protocol,
                    dest,
                    dest_interface,
                    next_hop
                ])
    return routes_with_next_hop

def save_routes_with_next_hop(routes_with_next_hop, db_path=PROTO_DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS proto_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_router TEXT,
            source_interface TEXT,
            protocol TEXT,
            destination TEXT,
            dest_interface TEXT,
            next_hop TEXT
        )
    ''')
    cur.execute('DELETE FROM proto_routes')
    for row in routes_with_next_hop:
        cur.execute('INSERT INTO proto_routes (source_router, source_interface, protocol, destination, dest_interface, next_hop) VALUES (?, ?, ?, ?, ?, ?)', row)
    conn.commit()
    conn.close()

# Main function to run all steps
def process_and_save_connections():
    router_data = get_router_data_from_rib()
    interface_info = extract_interface_info(router_data)
    direct_links = find_direct_connections(interface_info)
    save_direct_connections(direct_links)
    routes_with_next_hop = extract_routes_with_next_hop(router_data, interface_info)
    save_routes_with_next_hop(routes_with_next_hop)
    # Optional: print for debug
    print("="*80)
    print("DIRECTLY CONNECTED ROUTER INTERFACES (EXCLUDING LOOPBACKS)")
    print("="*80)
    print(tabulate(direct_links, headers=["Source Router", "Source IP", "Source Interface", "Dest Interface", "Dest IP", "Dest Router"], tablefmt="grid"))
    print("\n" + "="*80)
    print("PART 2: ROUTING TABLE WITH NEXT HOPS")
    print("="*80)
    print(tabulate(routes_with_next_hop, headers=["Source Router", "Source Interface", "Protocol", "Destination", "Destination Interface", "Next Hop"], tablefmt="grid"))
    print("\nAnalysis complete.")

if __name__ == "__main__":
    process_and_save_connections() 