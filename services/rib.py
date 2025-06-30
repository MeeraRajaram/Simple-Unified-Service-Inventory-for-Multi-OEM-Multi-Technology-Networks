"""
Module: rib.py
Purpose: Provides functions for accessing and managing RIB (Routing Information Base) data.
"""

import sqlite3
from typing import List, Dict, Any

def get_rib_entries(router_ip: str) -> List[Dict[str, Any]]:
    """
    Get RIB entries for a specific router.
    Args:
        router_ip (str): Router's IP address
    Returns:
        list: List of RIB entries with their details
    """
    try:
        conn = sqlite3.connect('rib_db.sqlite3')
        cursor = conn.cursor()
        
        # Get RIB entries for the router
        cursor.execute("""
            SELECT destination, next_hop, interface, protocol, metric
            FROM rib_entries
            WHERE router_ip = ?
        """, (router_ip,))
        
        entries = []
        for row in cursor.fetchall():
            entries.append({
                'destination': row[0],
                'next_hop': row[1],
                'interface': row[2],
                'protocol': row[3],
                'metric': row[4]
            })
            
        conn.close()
        return entries
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

def add_rib_entry(router_ip: str, entry: Dict[str, Any]) -> bool:
    """
    Add a new RIB entry for a router.
    Args:
        router_ip (str): Router's IP address
        entry (dict): RIB entry details
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect('rib_db.sqlite3')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO rib_entries (
                router_ip, destination, next_hop, interface, protocol, metric
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            router_ip,
            entry.get('destination'),
            entry.get('next_hop'),
            entry.get('interface'),
            entry.get('protocol'),
            entry.get('metric')
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def clear_rib_entries(router_ip: str) -> bool:
    """
    Clear all RIB entries for a specific router.
    Args:
        router_ip (str): Router's IP address
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect('rib_db.sqlite3')
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM rib_entries WHERE router_ip = ?", (router_ip,))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False 