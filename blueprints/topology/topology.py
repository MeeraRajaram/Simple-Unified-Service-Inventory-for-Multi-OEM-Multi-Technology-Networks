import sqlite3
import os
from flask import Blueprint, render_template, jsonify
import math
import ipaddress
from .protocol_utils import build_proto_routes_and_ospfdb

topology_bp = Blueprint('topology', __name__)

DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'directconndb'))
INIP_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inip.db'))
PROTO_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'protodb'))
PROTO_ROUTES_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'proto_routes.db'))
OSPF_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ospfdb'))
RIB_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'rib_db.sqlite3'))

# --- New Logic for proto_routes.db and ospfdb ---
# Call this function at appropriate place (e.g., after RIB/INIP/protodb update)
build_proto_routes_and_ospfdb(INIP_DB_PATH, PROTO_DB_PATH, PROTO_ROUTES_DB_PATH, OSPF_DB_PATH)

@topology_bp.route('/topology')
def topo_landing():
    return render_template('topology/topo_visualization.html')

@topology_bp.route('/topology/basic')
def topo_visualization():
    # Paths
    DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'directconndb'))
    INIP_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inip.db'))
    PROTO_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'protodb'))

    # Read direct connections from DB
    conn = sqlite3.connect(DIRECTCONN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router FROM direct_connections")
    rows = cur.fetchall()
    conn.close()

    # Build unique router list
    routers = {}
    for src_router, src_ip, src_iface, dst_iface, dst_ip, dst_router in rows:
        routers[src_router] = src_ip
        routers[dst_router] = dst_ip

    # Assign fixed positions in a circle with more spacing
    N = len(routers)
    radius = 500  # Increased spacing
    center_x, center_y = 0, 0
    node_list = []
    for idx, (router, ip) in enumerate(sorted(routers.items())):
        angle = 2 * math.pi * idx / N
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        node_list.append({
            "id": router,
            "label": f"{router}",  # Only generic name
            "x": x,
            "y": y,
            "fixed": True
        })

    # Build edges, avoiding duplicates (undirected)
    seen = set()
    edges = []
    for src_router, src_ip, src_iface, dst_iface, dst_ip, dst_router in rows:
        key = tuple(sorted([src_router, dst_router]))
        if key in seen:
            continue
        seen.add(key)
        label = f"{src_iface}({src_ip})\n<---->\n{dst_iface}({dst_ip})"
        edges.append({
            "from": src_router,
            "to": dst_router,
            "label": label,
            "font": {"align": "middle", "size": 14}
        })

    # Fetch INIP table
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT router_name, interface, ip FROM inip")
    inip_rows = cur.fetchall()
    conn.close()

    # Fetch direct_connections table
    conn = sqlite3.connect(DIRECTCONN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router FROM direct_connections")
    directconn_rows = cur.fetchall()
    conn.close()

    # Fetch proto_routes table
    conn = sqlite3.connect(PROTO_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_interface, protocol, destination, dest_interface, next_hop FROM proto_routes")
    proto_rows = cur.fetchall()
    conn.close()

    return render_template(
        'topology/topology_view.html',
        nodes=node_list,
        edges=edges,
        inip_rows=inip_rows,
        directconn_rows=directconn_rows,
        proto_rows=proto_rows
    )

def build_protocol_topology_nodes_edges():
    # Paths
    INIP_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inip.db'))
    PROTO_ROUTES_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'proto_routes.db'))
    DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'directconndb'))
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
    # Load direct connections (basic topology)
    conn = sqlite3.connect(DIRECTCONN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router FROM direct_connections")
    direct_rows = cur.fetchall()
    conn.close()
    # Build unique router list for node positions
    routers = set()
    for src_router, src_ip, src_iface, dst_iface, dst_ip, dst_router in direct_rows:
        routers.add(src_router)
        routers.add(dst_router)
    routers = sorted(list(routers))
    node_list = []
    for router in routers:
        node = {'id': router, 'label': router}
        node_list.append(node)
    # Add foreign network nodes as needed
    foreign_nodes = set()
    # Basic topology edges
    basic_edges = []
    seen = set()
    for src_router, src_ip, src_iface, dst_iface, dst_ip, dst_router in direct_rows:
        key = tuple(sorted([src_router, dst_router, src_ip, dst_ip]))
        if key in seen:
            continue
        seen.add(key)
        label = f"{src_iface}({src_ip}) <-> {dst_iface}({dst_ip})"
        basic_edges.append({
            'from': src_router,
            'to': dst_router,
            'label': label,
            'color': {'color': '#888', 'highlight': '#888', 'inherit': False},
            'font': {'align': 'middle', 'size': 14},
            'width': 2,
            'dashes': True
        })
    # Protocol edges: read from proto_routes.db, deduplicate
    conn = sqlite3.connect(PROTO_ROUTES_DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT source_router, source_interface, protocol, destination, dest_interface, next_hop, dest_router FROM proto_routes')
    proto_rows = cur.fetchall()
    conn.close()
    proto_edges = []
    proto_seen = set()
    protocol_colors = {
        'OSPF': '#e67e22',
        'Static': '#e74c3c',
        'BGP': '#8e44ad',
        'Connected': '#3498db',
        'Local': '#2ecc71',
        'Direct': '#16a085'
    }
    for src_router, src_iface, protocol, dest, dest_iface, next_hop, dest_router in proto_rows:
        key = (src_router, dest_router if dest_router else dest, protocol, src_iface, next_hop)
        if key in proto_seen:
            continue
        proto_seen.add(key)
        color = protocol_colors.get(protocol, '#333')
        # Add foreign node if needed
        to_node = dest_router if dest_router else dest
        if to_node not in routers and to_node not in foreign_nodes:
            node_list.append({'id': to_node, 'label': to_node})
            foreign_nodes.add(to_node)
        # Build label dynamically
        label = f"{protocol} | {src_iface} | Next Hop: {next_hop}"
        proto_edges.append({
            'from': src_router,
            'to': to_node,
            'label': label,
            'color': {'color': color, 'highlight': color, 'inherit': False},
            'font': {'color': color, 'size': 20, 'bold': True},
            'width': 5,
            'arrows': 'to'
        })
    all_edges = basic_edges + proto_edges
    return node_list, all_edges

@topology_bp.route('/topology/protocol')
def protocol_topology():
    node_list, edges = build_protocol_topology_nodes_edges()
    conn = sqlite3.connect(PROTO_ROUTES_DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT source_router, source_interface, protocol, destination, dest_interface, next_hop, dest_router FROM proto_routes')
    proto_routes_rows = cur.fetchall()
    conn.close()
    return render_template('topology/protocol_topology_view.html', nodes=node_list, edges=edges, proto_routes_rows=proto_routes_rows)

@topology_bp.route('/api/protocol-topology')
def api_protocol_topology():
    node_list, edges = build_protocol_topology_nodes_edges()
    conn = sqlite3.connect(PROTO_ROUTES_DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT source_router, destination, protocol, source_interface, dest_interface, next_hop FROM proto_routes')
    proto_routes_rows = cur.fetchall()
    conn.close()
    return jsonify({
        'nodes': node_list,
        'edges': edges,
        'proto_routes_rows': proto_routes_rows
    })

@topology_bp.route('/topology/inip/<router_name>')
def get_router_inip(router_name):
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT interface, ip FROM inip WHERE router_name = ?", (router_name,))
    rows = cur.fetchall()
    conn.close()
    return jsonify({
        "router_name": router_name,
        "interfaces": [
            {"interface": iface, "ip": ip} for iface, ip in rows
        ]
    })

# Load INIP table
def load_inip(inip_db_path):
    conn = sqlite3.connect(inip_db_path)
    cur = conn.cursor()
    cur.execute("SELECT router_name, interface, ip FROM inip")
    inip_rows = cur.fetchall()
    conn.close()
    ip_to_router_iface = {}
    router_iface_to_ip = {}
    for router, iface, ip in inip_rows:
        ip_to_router_iface[ip] = (router, iface)
        router_iface_to_ip[(router, iface)] = ip
    return ip_to_router_iface, router_iface_to_ip

# Parse protodb and build edges
def parse_protodb(protodb_path, inip_db_path):
    ip_to_router_iface, router_iface_to_ip = load_inip(inip_db_path)
    conn = sqlite3.connect(protodb_path)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_interface, protocol, destination, dest_interface, next_hop FROM proto_routes")
    proto_rows = cur.fetchall()
    conn.close()
    nodes = set()
    edges = []
    for src_router, src_iface, protocol, dest, dest_iface, next_hop in proto_rows:
        # Get source interface IP
        src_ip = router_iface_to_ip.get((src_router, src_iface), "Unknown")
        # Check if destination is in INIP
        dest_router, dest_router_iface = ip_to_router_iface.get(dest.split('/')[0], (None, None))
        if dest_router:
            # Destination is a known router
            nodes.add(src_router)
            nodes.add(dest_router)
            edge = {
                'from': src_router,
                'to': dest_router,
                'label': f"{protocol} | {src_iface} ({src_ip}) | Next Hop: {next_hop}"
            }
            edges.append(edge)
        else:
            # Foreign network or unknown destination
            net_node = dest.split('/')[0]
            nodes.add(src_router)
            nodes.add(net_node)
            edge = {
                'from': src_router,
                'to': net_node,
                'label': f"{protocol} | {src_iface} ({src_ip}) | Next Hop: {next_hop}"
            }
            edges.append(edge)
    return list(nodes), edges

def save_proto_routes_to_db(proto_edges):
    conn = sqlite3.connect(PROTO_ROUTES_DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS proto_routes (
        source_router TEXT,
        destination TEXT,
        label TEXT,
        source_interface TEXT,
        source_ip TEXT,
        next_hop TEXT
    )''')
    cur.execute('DELETE FROM proto_routes')
    proto_seen = set()
    for edge in proto_edges:
        # Parse label for protocol, interface, ip, next hop
        label_parts = edge['label'].split(' | ')
        protocol = label_parts[0] if len(label_parts) > 0 else ''
        src_iface = label_parts[1].split(' ')[0] if len(label_parts) > 1 else ''
        src_ip = label_parts[1].split('(')[-1].split(')')[0] if len(label_parts) > 1 and '(' in label_parts[1] and ')' in label_parts[1] else ''
        next_hop = label_parts[2].split('Next Hop: ')[-1] if len(label_parts) > 2 and 'Next Hop: ' in label_parts[2] else ''
        key = (edge['from'], edge['to'], protocol, src_iface, src_ip, next_hop)
        if key in proto_seen:
            continue
        proto_seen.add(key)
        cur.execute('''INSERT INTO proto_routes (source_router, destination, label, source_interface, source_ip, next_hop)
            VALUES (?, ?, ?, ?, ?, ?)''', (
            edge['from'],
            edge['to'],
            protocol,
            src_iface,
            src_ip,
            next_hop
        ))
    conn.commit()
    conn.close()

# Example usage:
nodes, edges = parse_protodb('protodb', 'inip.db')
for edge in edges:
    print(edge) 