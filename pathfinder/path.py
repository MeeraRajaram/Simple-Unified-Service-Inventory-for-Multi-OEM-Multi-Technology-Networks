import sqlite3
import os
import heapq
from collections import defaultdict, deque

RIB_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rib_db.sqlite3'))
INIP_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'inip.db'))
DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'directconndb'))
PROTODB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protodb'))
PATHFINDER_DIR = os.path.abspath(os.path.dirname(__file__))
PRIMARY_PATH_DB = os.path.join(PATHFINDER_DIR, 'primary_path.db')
ALTPATH_DB = os.path.join(PATHFINDER_DIR, 'altpath.db')
ALLPATHS_DB = os.path.join(PATHFINDER_DIR, 'allpaths.db')

# Helper: Build the network graph from directconndb
# Returns: graph[node] = list of (neighbor, interface, neighbor_interface, ip, neighbor_ip)
def build_graph():
    conn = sqlite3.connect(DIRECTCONN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router FROM direct_connections")
    edges = cur.fetchall()
    conn.close()
    graph = defaultdict(list)
    for src_router, src_ip, src_iface, dst_iface, dst_ip, dst_router in edges:
        graph[src_router].append((dst_router, src_iface, dst_iface, src_ip, dst_ip))
        graph[dst_router].append((src_router, dst_iface, src_iface, dst_ip, src_ip))  # undirected
    return graph

# Helper: Map IP to router name using inip.db
def ip_to_router(ip):
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT router_name, interface FROM inip WHERE ip = ?", (ip,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None

# Helper: Find all loopbacks for a router
def get_loopback(router_name):
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT ip FROM inip WHERE router_name = ? AND interface LIKE 'Loopback%'", (router_name,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows] if rows else []

# Helper: Find all interfaces and IPs for a router
def get_interfaces(router_name):
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT interface, ip FROM inip WHERE router_name = ?", (router_name,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Helper: Find all next hops from RIB for a router
def get_rib_next_hops(router_name):
    conn = sqlite3.connect(RIB_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT destination, next_hop, interface FROM rib WHERE router = ?", (router_name,))
    rows = cur.fetchall()
    conn.close()
    return rows

# Helper: Check protocol connection between two routers
# Looks for a row in proto_routes where source_router and next_hop match the two routers
# Returns protocol if found, else None
def get_protocol_between(router1, router2):
    conn = sqlite3.connect(PROTODB_PATH)
    cur = conn.cursor()
    # Try both directions
    cur.execute("SELECT protocol FROM proto_routes WHERE (source_router = ? AND next_hop = ?) OR (source_router = ? AND next_hop = ?)", (router1, router2, router2, router1))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0]
    return None

# Dijkstra's algorithm for shortest path, returns all paths as list of hops
# Each hop: (router_name, entry_iface, entry_ip, exit_iface, exit_ip, loopback, connection_type)
def dijkstra_all_paths(graph, src_router, dst_router, max_paths=10):
    # Standard Dijkstra for shortest path
    queue = [(0, [src_router])]
    visited = set()
    shortest_paths = []
    all_paths = []
    while queue and len(shortest_paths) < max_paths:
        cost, path = heapq.heappop(queue)
        node = path[-1]
        if (tuple(path)) in visited:
            continue
        visited.add(tuple(path))
        if node == dst_router:
            if path not in shortest_paths:
                shortest_paths.append(list(path))
            all_paths.append(list(path))
            continue
        for neighbor, *_ in graph[node]:
            if neighbor not in path:
                heapq.heappush(queue, (cost+1, path + [neighbor]))
    return shortest_paths, all_paths

# Store path info in DB
def store_paths(paths, db_path, src_ip, dst_ip):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS path (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hop INTEGER,
        router_name TEXT,
        entry_interface TEXT,
        entry_ip TEXT,
        exit_interface TEXT,
        exit_ip TEXT,
        loopback TEXT,
        connection_type TEXT,
        src_ip TEXT,
        dst_ip TEXT
    )''')
    cur.execute('DELETE FROM path')
    for path in paths:
        for hop_idx, hop in enumerate(path):
            router_name = hop['router_name']
            entry_iface = hop.get('entry_interface')
            entry_ip = hop.get('entry_ip')
            exit_iface = hop.get('exit_interface')
            exit_ip = hop.get('exit_ip')
            loopback = hop.get('loopback')
            connection_type = hop.get('connection_type')
            cur.execute('INSERT INTO path (hop, router_name, entry_interface, entry_ip, exit_interface, exit_ip, loopback, connection_type, src_ip, dst_ip) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                        (hop_idx, router_name, entry_iface, entry_ip, exit_iface, exit_ip, loopback, connection_type, src_ip, dst_ip))
    conn.commit()
    conn.close()

def dijkstra_shortest_path(graph, src, dst):
    # Standard Dijkstra for shortest path only
    queue = [(0, [src])]
    visited = set()
    while queue:
        cost, path = heapq.heappop(queue)
        node = path[-1]
        if node == dst:
            return path
        if (tuple(path)) in visited:
            continue
        visited.add(tuple(path))
        for neighbor, *_ in graph[node]:
            if neighbor not in path:
                heapq.heappush(queue, (cost+1, path + [neighbor]))
    return None

def find_all_simple_paths(graph, src, dst, max_paths=20, exclude_path=None):
    # BFS to find all simple paths from src to dst (up to max_paths), optionally excluding a given path
    queue = deque([[src]])
    paths = []
    while queue and len(paths) < max_paths:
        path = queue.popleft()
        node = path[-1]
        if node == dst:
            if exclude_path is None or path != exclude_path:
                paths.append(list(path))
            continue
        for neighbor, *_ in graph[node]:
            if neighbor not in path:
                queue.append(path + [neighbor])
    return paths

def find_paths(src_ip, dst_ip):
    # 1. Map IPs to routers
    src_router, src_iface = ip_to_router(src_ip)
    dst_router, dst_iface = ip_to_router(dst_ip)
    if not src_router or not dst_router:
        return {'error': 'Source or destination IP not found in INIP DB.'}
    # 2. Build graph
    graph = build_graph()
    # 3. Find primary path using Dijkstra
    primary_path = dijkstra_shortest_path(graph, src_router, dst_router)
    # 4. Find all unique alternate paths (excluding primary)
    alternates = []
    if primary_path:
        alternates = find_all_simple_paths(graph, src_router, dst_router, max_paths=20, exclude_path=primary_path)
    # Remove duplicates
    unique_alternates = []
    seen = set()
    for p in alternates:
        key = tuple(p)
        if key not in seen:
            unique_alternates.append(p)
            seen.add(key)
    # 5. For each path, build hop info
    def build_hop_info(path):
        hops = []
        for idx, router in enumerate(path):
            hop = {'router_name': router, 'loopback': None, 'entry_interface': None, 'entry_ip': None, 'exit_interface': None, 'exit_ip': None, 'connection_type': None}
            hop['loopback'] = ','.join(get_loopback(router))
            if idx == 0:
                hop['entry_interface'] = src_iface
                hop['entry_ip'] = src_ip
            else:
                prev_router = path[idx-1]
                for edge in graph[prev_router]:
                    if edge[0] == router:
                        hop['entry_interface'] = edge[2]
                        hop['entry_ip'] = edge[4]
                        break
            if idx < len(path)-1:
                next_router = path[idx+1]
                for edge in graph[router]:
                    if edge[0] == next_router:
                        hop['exit_interface'] = edge[1]
                        hop['exit_ip'] = edge[3]
                        break
                protocol = get_protocol_between(router, next_router)
                if protocol:
                    hop['connection_type'] = protocol
                else:
                    hop['connection_type'] = 'directly connected'
            else:
                hop['connection_type'] = None  # Last hop (destination)
            hops.append(hop)
        return hops
    # 6. Store primary path and alternates
    if primary_path:
        store_paths([build_hop_info(primary_path)], PRIMARY_PATH_DB, src_ip, dst_ip)
    if unique_alternates:
        store_paths([build_hop_info(p) for p in unique_alternates], ALTPATH_DB, src_ip, dst_ip)
    if primary_path or unique_alternates:
        all_paths = ([primary_path] if primary_path else []) + unique_alternates
        store_paths([build_hop_info(p) for p in all_paths], ALLPATHS_DB, src_ip, dst_ip)
    return {
        'primary': [build_hop_info(primary_path)] if primary_path else [],
        'alternates': [build_hop_info(p) for p in unique_alternates],
        'all': [build_hop_info(p) for p in ([primary_path] if primary_path else []) + unique_alternates]
    } 