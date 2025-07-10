import sqlite3
import os
from typing import List, Dict, Tuple

def store_path_data(path_hops: List[Dict], label: str = None, path_type: str = None):
    """
    Store the path information hop-by-hop in path.db and print the path as a list of dictionaries and as a router: (entry_ip, exit_interface) dict.
    Each hop dict should contain at least:
        - router_name
        - entry_ip (can be empty for the first hop)
        - exit_interface
    Args:
        path_hops (List[Dict]): List of hop dictionaries in order from source to destination.
        label (str): Optional label to print before the dictionary.
        path_type (str): Optional type to store in the db (e.g., 'primary', 'alternate1').
    """
    PATH_DB = os.path.join(os.path.dirname(__file__), 'path.db')
    conn = sqlite3.connect(PATH_DB)
    cur = conn.cursor()
    cur.execute('DROP TABLE IF EXISTS path')
    cur.execute('''CREATE TABLE path (
        hop INTEGER,
        router_name TEXT,
        entry_ip TEXT,
        exit_interface TEXT,
        path_type TEXT
    )''')
    if path_type is None:
        path_type = ''
    for idx, hop in enumerate(path_hops):
        cur.execute('INSERT INTO path (hop, router_name, entry_ip, exit_interface, path_type) VALUES (?, ?, ?, ?, ?)',
                    (idx, hop.get('router_name'), hop.get('entry_ip', ''), hop.get('exit_interface', ''), path_type))
    conn.commit()
    conn.close()
    # Print the path as a router: (entry_ip, exit_interface) dict
    path_dict = {}
    for hop in path_hops:
        path_dict[hop.get('router_name')] = (hop.get('entry_ip', ''), hop.get('exit_interface', ''))
    if label:
        print(f"\n{label} as dictionary (router_name: (entry_ip, exit_interface)):")
    else:
        print("\nPath as dictionary (router_name: (entry_ip, exit_interface)):")
    print(path_dict)

def store_multiple_paths(labeled_paths: List[Tuple[str, List[Dict]]]):
    """
    Store and print multiple paths, each with a label.
    Args:
        labeled_paths: List of (label, path_hops) pairs.
    """
    for idx, (label, path_hops) in enumerate(labeled_paths):
        path_type = 'primary' if idx == 0 else f'alternate{idx}'
        store_path_data(path_hops, label=label, path_type=path_type) 