"""
services/db.py
--------------
Database management module for network automation web app.
Provides thread-safe access to the routers and router_routes tables in SQLite.
Handles router inventory, lookup history, and atomic updates for live discovery.
"""

import sqlite3
from threading import Lock
import os

class RouterDB:
    """
    Thread-safe database handler for router inventory and lookup history.
    Manages the routers table (live inventory) and router_routes table (lookup history).
    """
    def __init__(self, db_path='routers.db'):
        """
        Initialize the RouterDB instance and create tables if needed.
        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.lock = Lock()
        self._migrate_table()
        self._create_table()

    def _create_table(self):
        """
        Create the routers and router_routes tables if they do not exist.
        """
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
        """
        Add missing columns to the routers table if needed (e.g., software_version).
        """
        with self.conn:
            cur = self.conn.cursor()
            cur.execute("PRAGMA table_info(routers)")
            columns = [row[1] for row in cur.fetchall()]
            if 'software_version' not in columns:
                cur.execute('ALTER TABLE routers ADD COLUMN software_version TEXT')
                self.conn.commit()

    def add_router(self, hostname, software_version, ip, vendor, username, password):
        """
        Add or update a router in the routers table.
        Args:
            hostname (str): Router hostname.
            software_version (str): Software version.
            ip (str): Router IP address.
            vendor (str): Vendor name.
            username (str): Management username.
            password (str): Management password.
        """
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
        """
        Get all routers in the inventory.
        Returns:
            list: List of tuples (hostname, software_version, ip, vendor, username, password)
        """
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('SELECT hostname, software_version, ip, vendor, username, password FROM routers')
            return cur.fetchall()

    def get_latest_routers(self):
        """
        Get all routers, ordered by last_updated (most recent first).
        Returns:
            list: List of tuples (hostname, software_version, ip, vendor, username, password)
        """
        with self.lock:
            cur = self.conn.cursor()
            cur.execute('''
                SELECT hostname, software_version, ip, vendor, username, password
                FROM routers
                ORDER BY last_updated DESC
            ''')
            return cur.fetchall()

    def clear(self):
        """
        Remove all routers from the inventory.
        """
        with self.lock:
            self.conn.execute('DELETE FROM routers')
            self.conn.commit()

    def add_router_route(self, source_ip, source_router, source_vendor, source_interface,
                        dest_ip, dest_router, dest_vendor, dest_interface):
        """
        Add a lookup history entry to router_routes.
        Args:
            source_ip (str): Source IP.
            source_router (str): Source router name.
            source_vendor (str): Source vendor.
            source_interface (str): Source interface.
            dest_ip (str): Destination IP.
            dest_router (str): Destination router name.
            dest_vendor (str): Destination vendor.
            dest_interface (str): Destination interface.
        """
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
        """
        Get the most recent router lookup history entries.
        Args:
            limit (int): Maximum number of entries to return.
        Returns:
            list: List of tuples with router route history.
        """
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