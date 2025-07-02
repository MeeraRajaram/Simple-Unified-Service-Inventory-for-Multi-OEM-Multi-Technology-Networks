import sqlite3
import os
from flask import Blueprint, render_template

view_bp = Blueprint('view', __name__)

DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'directconndb'))

@view_bp.route('/topology')
def topology():
    # Read direct connections from DB
    conn = sqlite3.connect(DIRECTCONN_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router FROM direct_connections")
    rows = cur.fetchall()
    conn.close()

    # Build nodes and edges for vis-network
    nodes = {}
    edges = []
    for src_router, src_ip, src_iface, dst_iface, dst_ip, dst_router in rows:
        if src_router not in nodes:
            nodes[src_router] = {"id": src_router, "label": f"{src_router}\n{src_ip}"}
        if dst_router not in nodes:
            nodes[dst_router] = {"id": dst_router, "label": f"{dst_router}\n{dst_ip}"}
        label = f"{src_iface}({src_ip}) <-> {dst_iface}({dst_ip})"
        edges.append({
            "from": src_router,
            "to": dst_router,
            "label": label
        })

    print("NODES:", list(nodes.values()))
    print("EDGES:", edges)

    return render_template("topology/topology_view.html", nodes=list(nodes.values()), edges=edges)