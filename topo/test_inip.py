import sqlite3
import os
from tabulate import tabulate
from collections import defaultdict

# Always use the rib_db.sqlite3 in the project root
RIB_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rib_db.sqlite3'))

def print_inip_table(db_path=RIB_DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT router_name, interface, ip FROM inip")
        rows = cur.fetchall()
        print("\nINIP TABLE:")
        print(tabulate(rows, headers=["Router Name", "Interface", "IP"], tablefmt="grid"))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("\nINIP TABLE does not exist in the database.")
        else:
            raise
    finally:
        conn.close()

def print_rib_table(db_path=RIB_DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT router, loopback_ip, protocol, destination, interface, next_hop FROM rib")
        rows = cur.fetchall()
        print("\nRIB TABLE:")
        print(tabulate(rows, headers=["Router", "Loopback IP", "Protocol", "Destination", "Interface", "Next Hop"], tablefmt="grid"))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("\nRIB TABLE does not exist in the database.")
        else:
            raise
    finally:
        conn.close()

def print_consolidated_local_ips_table(db_path=RIB_DB_PATH):
    """
    Print a single consolidated table of all routers, their interfaces, and local IPs.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT router, loopback_ip, protocol, destination, interface, next_hop FROM rib")
        rows = cur.fetchall()
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
        print("\nConsolidated Local IPs Table:")
        print(tabulate(consolidated, headers=["Router Name (Generic)", "Interface", "IP"], tablefmt="grid"))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("\nRIB TABLE does not exist in the database.")
        else:
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    print_rib_table()
    print_inip_table()
    print_consolidated_local_ips_table() 