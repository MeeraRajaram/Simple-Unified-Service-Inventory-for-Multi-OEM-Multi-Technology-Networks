import sqlite3
import os
import ipaddress

def build_proto_routes_and_ospfdb(INIP_DB_PATH, PROTO_DB_PATH, PROTO_ROUTES_DB_PATH, OSPF_DB_PATH):
    """
    Build proto_routes.db and ospfdb from protodb and inip.db.
    - proto_routes.db: Contains protocol routes with deduplicated OSPF links and correct router mapping.
    - ospfdb: Contains unique OSPF neighbor pairs.
    Args:
        INIP_DB_PATH (str): Path to inip.db
        PROTO_DB_PATH (str): Path to protodb
        PROTO_ROUTES_DB_PATH (str): Path to proto_routes.db
        OSPF_DB_PATH (str): Path to ospfdb
    """
    # Load INIP
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT router_name, interface, ip FROM inip")
    inip_rows = cur.fetchall()
    conn.close()
    ip_to_router_iface = {}
    router_iface_to_ip = {}
    for router, iface, ip in inip_rows:
        ip_to_router_iface[ip] = (router, iface)
        router_iface_to_ip[(router, iface)] = ip

    # Load protodb
    conn = sqlite3.connect(PROTO_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_interface, protocol, destination, dest_interface, next_hop FROM proto_routes")
    proto_rows = cur.fetchall()
    conn.close()

    # Build proto_routes for proto_routes.db
    proto_routes_entries = []
    ospf_links = set()  # To deduplicate OSPF links
    for src_router, src_iface, protocol, dest, dest_iface, next_hop in proto_rows:
        src_ip = router_iface_to_ip.get((src_router, src_iface), "Unknown")
        dest_ip = dest.split('/')[0]
        dest_router = None
        for ip, (router, iface) in ip_to_router_iface.items():
            try:
                if '/' in dest:
                    net = ipaddress.ip_network(dest, strict=False)
                    if ipaddress.ip_address(ip) in net:
                        dest_router = router
                        break
                else:
                    if ip == dest:
                        dest_router = router
                        break
            except Exception:
                continue
        if protocol == 'OSPF' and dest_router:
            key = tuple(sorted([src_router, dest_router]))
            if key in ospf_links:
                continue
            ospf_links.add(key)
        proto_routes_entries.append((src_router, src_iface, protocol, dest, dest_iface, next_hop, dest_router))

    # Write to proto_routes.db (overwriting existing)
    conn = sqlite3.connect(PROTO_ROUTES_DB_PATH)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS proto_routes')
    cur.execute('''CREATE TABLE proto_routes (
        source_router TEXT,
        source_interface TEXT,
        protocol TEXT,
        destination TEXT,
        dest_interface TEXT,
        next_hop TEXT,
        dest_router TEXT
    )''')
    for row in proto_routes_entries:
        cur.execute('INSERT INTO proto_routes (source_router, source_interface, protocol, destination, dest_interface, next_hop, dest_router) VALUES (?, ?, ?, ?, ?, ?, ?)', row)
    conn.commit()
    conn.close()

    # --- Build OSPF neighbor table ---
    ospf_neighbors = set()
    for src_router, src_iface, protocol, dest, dest_iface, next_hop, dest_router in proto_routes_entries:
        if protocol == 'OSPF' and dest_router and src_router != dest_router:
            key = tuple(sorted([src_router, dest_router]))
            if key in ospf_neighbors:
                continue
            ospf_neighbors.add(key)
    # Write to ospfdb
    conn = sqlite3.connect(OSPF_DB_PATH)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS ospf_neighbors')
    cur.execute('''CREATE TABLE ospf_neighbors (
        router TEXT,
        neighbor TEXT
    )''')
    for router1, router2 in ospf_neighbors:
        cur.execute('INSERT INTO ospf_neighbors (router, neighbor) VALUES (?, ?)', (router1, router2))
    conn.commit()
    conn.close() 