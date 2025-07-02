import sqlite3
from threading import Lock
import os

class RouterDB:
    def __init__(self, db_path='routers.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = Lock()
        self._migrate_table()
        self._create_table()

    def _create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS routers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hostname TEXT,
                    software_version TEXT,
                    ip TEXT UNIQUE,
                    vendor TEXT,
                    username TEXT,
                    password TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # Create router_routes table for storing lookup history
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS router_routes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source_ip TEXT,
                    source_router TEXT,
                    source_vendor TEXT,
                    source_interface TEXT,
                    dest_ip TEXT,
                    dest_router TEXT,
                    dest_vendor TEXT,
                    dest_interface TEXT
                )
            ''')

    def _migrate_table(self):
        # Add software_version column if it doesn't exist
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("PRAGMA table_info(routers)")
            columns = [row[1] for row in cur.fetchall()]
            if 'software_version' not in columns:
                cur.execute('ALTER TABLE routers ADD COLUMN software_version TEXT')
                self.conn.commit()

    def add_router(self, hostname, software_version, ip, vendor, username, password):
        with self.lock:
            self.conn.execute(
                '''
                INSERT OR REPLACE INTO routers (hostname, software_version, ip, vendor, username, password, last_updated)
                VALUES (
                    COALESCE((SELECT hostname FROM routers WHERE ip = ?), ?),
                    COALESCE((SELECT software_version FROM routers WHERE ip = ?), ?),
                    ?, ?, ?, ?,
                    CURRENT_TIMESTAMP
                )
                ''',
                (ip, hostname, ip, software_version, ip, vendor, username, password)
            )
            self.conn.commit()

    def get_routers(self):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('SELECT hostname, software_version, ip, vendor, username, password FROM routers')
            return cur.fetchall()

    def get_latest_routers(self):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('''
                SELECT hostname, software_version, ip, vendor, username, password
                FROM routers
                ORDER BY last_updated DESC
            ''')
            return cur.fetchall()

    def clear(self):
        with self.lock:
            self.conn.execute('DELETE FROM routers')
            self.conn.commit()

    def add_router_route(self, source_ip, source_router, source_vendor, source_interface,
                        dest_ip, dest_router, dest_vendor, dest_interface):
        with self.lock:
            self.conn.execute('''
                INSERT INTO router_routes (
                    timestamp, source_ip, source_router, source_vendor, source_interface,
                    dest_ip, dest_router, dest_vendor, dest_interface
                ) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (source_ip, source_router, source_vendor, source_interface,
                  dest_ip, dest_router, dest_vendor, dest_interface))
            self.conn.commit()

    def get_router_routes(self, limit=50):
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('''
                SELECT timestamp, source_ip, source_router, source_vendor, source_interface,
                       dest_ip, dest_router, dest_vendor, dest_interface
                FROM router_routes
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            return cur.fetchall()

# Singleton instance
router_db = RouterDB() 