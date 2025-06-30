import sqlite3
from threading import Lock
import datetime

class RibDBManager:
    def __init__(self, db_path='rib_db.sqlite3'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = Lock()
        self._create_table()
        self._create_history_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS rib (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    router TEXT,
                    loopback_ip TEXT,
                    protocol TEXT,
                    destination TEXT,
                    interface TEXT,
                    next_hop TEXT,
                    UNIQUE(router, loopback_ip, protocol, destination, interface, next_hop)
                )
            ''')

    def _create_history_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS rib_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    draft_name TEXT,
                    timestamp TEXT,
                    router TEXT,
                    loopback_ip TEXT,
                    protocol TEXT,
                    destination TEXT,
                    interface TEXT,
                    next_hop TEXT
                )
            ''')

    def add_entry(self, router, loopback_ip, protocol, destination, interface, next_hop):
        with self.lock:
            self.conn.execute('''
                INSERT OR IGNORE INTO rib (router, loopback_ip, protocol, destination, interface, next_hop)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (router, loopback_ip, protocol, destination, interface, next_hop))
            self.conn.commit()

    def get_entries(self):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('SELECT router, loopback_ip, protocol, destination, interface, next_hop FROM rib')
            return cur.fetchall()

    def clear(self):
        with self.lock:
            self.conn.execute('DELETE FROM rib')
            self.conn.commit()

    def drop_and_recreate_table(self):
        with self.lock:
            self.conn.execute('DROP TABLE IF EXISTS rib')
            self.conn.commit()
            self._create_table()

    def remove_duplicates(self):
        with self.lock:
            # Keep only the first occurrence of each unique row (excluding id)
            self.conn.execute('''
                DELETE FROM rib WHERE id NOT IN (
                    SELECT MIN(id) FROM rib
                    GROUP BY router, loopback_ip, protocol, destination, interface, next_hop
                )
            ''')
            self.conn.commit()

    def save_rib_to_history(self):
        with self.lock:
            cur = self.conn.cursor()
            # Get next draft name
            cur.execute('SELECT COUNT(DISTINCT draft_name) FROM rib_history')
            count = cur.fetchone()[0] + 1
            draft_name = f'draftrib{count}'
            timestamp = datetime.datetime.now().isoformat()
            # Copy all current rib entries to history
            cur.execute('''
                INSERT INTO rib_history (draft_name, timestamp, router, loopback_ip, protocol, destination, interface, next_hop)
                SELECT ?, ?, router, loopback_ip, protocol, destination, interface, next_hop FROM rib
            ''', (draft_name, timestamp))
            self.conn.commit()
            return draft_name

    def get_history_drafts(self):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('SELECT DISTINCT draft_name, timestamp FROM rib_history ORDER BY id')
            return cur.fetchall()

    def get_history_entries(self, draft_name):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('''
                SELECT router, loopback_ip, protocol, destination, interface, next_hop
                FROM rib_history WHERE draft_name = ?
            ''', (draft_name,))
            return cur.fetchall()

rib_db_manage = RibDBManager()

if __name__ == "__main__":
    print("Dropping and recreating the rib table with full-row uniqueness...")
    rib_db_manage.drop_and_recreate_table()
    print("Done. Table is now unique on all columns except id.")
    print("Removing any existing duplicates (if any)...")
    rib_db_manage.remove_duplicates()
    print("Done. All duplicates removed.") 