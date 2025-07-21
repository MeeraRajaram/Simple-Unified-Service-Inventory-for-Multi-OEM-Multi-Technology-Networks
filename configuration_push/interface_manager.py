import sqlite3
import os
import re

INIP_DB = os.path.join(os.path.dirname(__file__), '..', 'inip.db')

INTERFACE_MAP = {
    'gi': 'GigabitEthernet',
    'ge': 'GigabitEthernet',
    'te': 'TenGigabitEthernet',
    'fa': 'FastEthernet',
    'lo': 'Loopback',
    'tu': 'Tunnel',
    'GigabitEthernet': 'GigabitEthernet',
    'TenGigabitEthernet': 'TenGigabitEthernet',
    'FastEthernet': 'FastEthernet',
    'Loopback': 'Loopback',
    'Tunnel': 'Tunnel',
}

# For demo: possible interface types and numbers (customize as needed)
POSSIBLE_INTF_TYPES = ['GigabitEthernet', 'TenGigabitEthernet', 'FastEthernet', 'Loopback']
POSSIBLE_INTF_NUMS = {
    'GigabitEthernet': [f'{i}' for i in range(1, 5)],
    'TenGigabitEthernet': [f'{i}/0/1' for i in range(1, 3)],
    'FastEthernet': [f'{i}' for i in range(0, 2)],
    'Loopback': [f'{i}' for i in range(0, 2)],
}

def normalize_interface(user_input):
    """
    Convert user input like gi1, te1/0/1, fa0, lo0 to canonical form (e.g., GigabitEthernet1)
    """
    match = re.match(r'^([a-zA-Z]+)([\d/]+)$', user_input)
    if not match:
        return user_input  # fallback
    intf_type, intf_num = match.groups()
    yang_type = INTERFACE_MAP.get(intf_type.lower(), intf_type.capitalize())
    return f"{yang_type}{intf_num}"

def get_free_interfaces(router_name):
    """
    Returns a list of free interfaces for the router (not present in inip.db)
    """
    used_interfaces = set()
    if os.path.exists(INIP_DB):
        conn = sqlite3.connect(INIP_DB)
        cur = conn.cursor()
        cur.execute("SELECT interface FROM inip WHERE router_name=?", (router_name,))
        rows = cur.fetchall()
        for row in rows:
            used_interfaces.add(row[0])
        conn.close()
    # Build all possible interfaces
    all_interfaces = set()
    for intf_type in POSSIBLE_INTF_TYPES:
        for intf_num in POSSIBLE_INTF_NUMS[intf_type]:
            all_interfaces.add(f"{intf_type}{intf_num}")
    free_interfaces = list(all_interfaces - used_interfaces)
    return sorted(free_interfaces) 