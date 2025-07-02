import sqlite3
import os
from tabulate import tabulate

# Paths to the databases
DIRECTCONN_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'directconndb'))
PROTO_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protodb'))

def print_direct_connections(db_path=DIRECTCONN_DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT source_router, source_ip, source_interface, dest_interface, dest_ip, dest_router FROM direct_connections")
        rows = cur.fetchall()
        print("\nDIRECTLY CONNECTED ROUTER INTERFACES (EXCLUDING LOOPBACKS):")
        print(tabulate(rows, headers=["Source Router", "Source IP", "Source Interface", "Dest Interface", "Dest IP", "Dest Router"], tablefmt="grid"))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("\nDIRECT CONNECTIONS TABLE does not exist in the database.")
        else:
            raise
    finally:
        conn.close()

def print_proto_routes(db_path=PROTO_DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("SELECT source_router, source_interface, protocol, destination, dest_interface, next_hop FROM proto_routes")
        rows = cur.fetchall()
        print("\nPART 2: ROUTING TABLE WITH NEXT HOPS:")
        print(tabulate(rows, headers=["Source Router", "Source Interface", "Protocol", "Destination", "Destination Interface", "Next Hop"], tablefmt="grid"))
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            print("\nPROTO ROUTES TABLE does not exist in the database.")
        else:
            raise
    finally:
        conn.close()

if __name__ == "__main__":
    print_direct_connections()
    print_proto_routes() 