import sqlite3
import os
from collections import defaultdict

# Always use the rib_db.sqlite3 in the project root
RIB_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rib_db.sqlite3'))
# Always use inip.db in the project root for storing INIP
INIP_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'inip.db'))

def build_and_store_inip_table():
    conn = sqlite3.connect(RIB_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT router, loopback_ip, protocol, destination, interface, next_hop FROM rib")
    rows = cur.fetchall()
    conn.close()
    # Build routers dict keyed by loopback_ip
    routers = defaultdict(list)
    for row in rows:
        router, loopback_ip, protocol, destination, interface, next_hop = row
        routers[loopback_ip].append(row)
    # Assign generic names
    router_names = {lb: f"Router{i}" for i, lb in enumerate(sorted(routers.keys()), 1)}
    # Build consolidated list
    consolidated = []
    for loopback, routes in routers.items():
        router_name = router_names[loopback]
        for route in routes:
            protocol = route[2]
            destination = route[3]
            interface = route[4]
            # Look for Connected, Local, or Direct routes
            if protocol in ['Connected', 'Local', 'Direct'] and interface and '/' in destination:
                ip = destination.split('/')[0]
                if ip not in ['0.0.0.0', '224.0.0.5']:
                    consolidated.append((router_name, interface, ip))
    # Store in inip.db
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS inip (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            router_name TEXT,
            interface TEXT,
            ip TEXT
        )
    ''')
    cur.execute('DELETE FROM inip')
    for row in consolidated:
        cur.execute('INSERT INTO inip (router_name, interface, ip) VALUES (?, ?, ?)', row)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    build_and_store_inip_table()
    print("inip.db created and populated.") 