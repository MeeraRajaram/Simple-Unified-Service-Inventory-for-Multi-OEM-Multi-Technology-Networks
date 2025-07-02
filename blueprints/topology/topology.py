import sqlite3
import os
from flask import Blueprint, render_template, jsonify
import math

topology_bp = Blueprint('topology', __name__)

DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'directconndb'))
INIP_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'inip.db'))
PROTO_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'protodb'))

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

@topology_bp.route('/topology/protocol')
def protocol_topology():
    # Paths
    DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'directconndb'))
    PROTO_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'protodb'))

    # Get all routers from directconndb for node positions
    conn = sqlite3.connect(DIRECTCONN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT source_router, source_ip FROM direct_connections")
    routers = {row[0]: row[1] for row in cur.fetchall()}
    conn.close()

    # Assign fixed positions in a circle
    N = len(routers)
    radius = 600
    node_list = []
    for idx, (router, ip) in enumerate(sorted(routers.items())):
        angle = 2 * math.pi * idx / N
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        node_list.append({
            "id": router,
            "label": f"{router}",
            "x": x,
            "y": y,
            "fixed": True,
            "size": 50
        })

    # --- Direct connections (basic topology) ---
    conn = sqlite3.connect(DIRECTCONN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router FROM direct_connections")
    direct_edges_raw = cur.fetchall()
    conn.close()
    seen = set()
    direct_edges = []
    for src_router, src_ip, src_iface, dst_iface, dst_ip, dst_router in direct_edges_raw:
        key = tuple(sorted([src_router, dst_router]))
        if key in seen:
            continue
        seen.add(key)
        label = f"{src_iface}({src_ip}) <-> {dst_iface}({dst_ip})"
        direct_edges.append({
            "from": src_router,
            "to": dst_router,
            "label": label,
            "color": {"color": "#888", "highlight": "#888", "inherit": False},
            "font": {"color": "#444", "size": 16},
            "width": 2,
            "dashes": True
        })

    # --- Protocol connections ---
    conn = sqlite3.connect(PROTO_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_interface, protocol, destination, dest_interface, next_hop FROM proto_routes")
    proto_edges_raw = cur.fetchall()
    conn.close()
    protocol_colors = {
        'OSPF': '#e67e22',
        'Static': '#e74c3c',
        'BGP': '#8e44ad',
        'Connected': '#3498db',
        'Local': '#2ecc71',
        'Direct': '#16a085'
    }
    proto_edges = []
    for src_router, src_iface, protocol, dest, dest_iface, next_hop in proto_edges_raw:
        color = protocol_colors.get(protocol, '#333')
        # Find the destination router by matching dest with a router IP
        dest_router = None
        for r, ip in routers.items():
            if dest.startswith(ip):
                dest_router = r
                break
        if not dest_router or dest_router == src_router:
            continue  # skip if can't match or self-loop
        label = f"{protocol}\n{src_iface}→{dest_iface}"
        proto_edges.append({
            "from": src_router,
            "to": dest_router,
            "label": label,
            "color": {"color": color, "highlight": color, "inherit": False},
            "font": {"color": color, "size": 20, "bold": True},
            "width": 5,
            "arrows": "to"
        })

    # Combine both edge types (protocol edges last so they are on top)
    edges = direct_edges + proto_edges

    return render_template('topology/protocol_topology_view.html', nodes=node_list, edges=edges)

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