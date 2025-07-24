"""
l3vpn/vrf_db_manager.py
-----------------------
VRF database management module for network automation web app.
Handles creation, clearing, population, and retrieval of VRF configuration data in vrf.db, using router data from push_data.db.
"""

import sqlite3
import os

VRF_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'vrf.db')
PUSH_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'push_data.db')

def init_vrf_db():
    """
    Initialize the vrf.db database and create the vrf table if it does not exist.
    """
    conn = sqlite3.connect(VRF_DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS vrf (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            router_name TEXT,
            router_loopback_ip TEXT,
            vrf_name TEXT,
            rd TEXT,
            rt TEXT,
            description TEXT,
            netconf_username TEXT,
            netconf_password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def clear_vrf_db():
    """
    Clear all rows from the vrf table in vrf.db.
    """
    conn = sqlite3.connect(VRF_DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM vrf')
    conn.commit()
    conn.close()

def populate_vrf_db(vrf_name, rd, rt, description, username, password):
    """
    Populate vrf.db with one row per router in push_data.db, using common VRF details.

    Args:
        vrf_name (str): VRF name (common for all routers).
        rd (str): Route Distinguisher (common).
        rt (str): Route Target(s) (common).
        description (str): VRF description (common).
        username (str): NETCONF username.
        password (str): NETCONF password.
    """
    conn_push = sqlite3.connect(PUSH_DB_PATH)
    c_push = conn_push.cursor()
    c_push.execute('SELECT router_name, router_loopback_ip FROM push_data')
    routers = c_push.fetchall()
    conn_push.close()

    conn_vrf = sqlite3.connect(VRF_DB_PATH)
    c_vrf = conn_vrf.cursor()
    for router_name, router_loopback_ip in routers:
        c_vrf.execute('''
            INSERT INTO vrf (router_name, router_loopback_ip, vrf_name, rd, rt, description, netconf_username, netconf_password)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (router_name, router_loopback_ip, vrf_name, rd, rt, description, username, password))
    conn_vrf.commit()
    conn_vrf.close()

def fetch_all_vrf_rows():
    """
    Fetch all rows from the vrf table in vrf.db.

    Returns:
        list: List of tuples containing all columns for each VRF row.
    """
    conn = sqlite3.connect(VRF_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT router_name, router_loopback_ip, vrf_name, rd, rt, description, netconf_username, netconf_password FROM vrf')
    rows = c.fetchall()
    conn.close()
    return rows 