import sqlite3
import os

INIP_DB = os.path.join(os.path.dirname(__file__), '..', 'inip.db')
RIB_DB = os.path.join(os.path.dirname(__file__), '..', 'rib_db.sqlite3')

def get_loopback(router_name):
    # 1. Try inip.db first
    if os.path.exists(INIP_DB):
        try:
            conn = sqlite3.connect(INIP_DB)
            cur = conn.cursor()
            cur.execute("SELECT ip FROM inip WHERE router_name=? AND interface='Loopback0'", (router_name,))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                return row[0]
        except Exception:
            pass
    # 2. Try rib_db.sqlite3 if not found in inip.db
    if os.path.exists(RIB_DB):
        try:
            conn = sqlite3.connect(RIB_DB)
            cur = conn.cursor()
            cur.execute("SELECT destination FROM rib WHERE router=? AND interface='Loopback0'", (router_name,))
            row = cur.fetchone()
            conn.close()
            if row and row[0]:
                # destination might be like '192.168.0.3/32', strip /32 if present
                return row[0].split('/')[0]
        except Exception:
            pass
    return None

def get_loopbacks(router_names):
    return {name: get_loopback(name) for name in router_names} 

def print_push_data():
    """Print all rows in push_data table to the console for debugging."""
    print(f"Using DB_PATH: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Check if table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='push_data'")
        if not c.fetchone():
            print("Table 'push_data' does not exist in the database.")
            return
        c.execute('SELECT * FROM push_data')
        rows = c.fetchall()
        conn.close()
        print('push_data table rows:')
        if not rows:
            print('(No rows found)')
        for row in rows:
            print(row)
    except Exception as e:
        print('Error printing push_data table:', str(e))

if __name__ == '__main__':
    print_push_data() 