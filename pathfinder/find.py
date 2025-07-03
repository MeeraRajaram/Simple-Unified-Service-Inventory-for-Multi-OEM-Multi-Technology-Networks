import sqlite3
import os
from services.vendor_host import get_device_info

RIB_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'rib_db.sqlite3'))
INIP_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'inip.db'))

# You may want to set these as your default NETCONF credentials
NETCONF_PORT = 830
NETCONF_USERNAME = "admin"
NETCONF_PASSWORD = "admin"

def find_ip_info(ip):
    # 1. Check if IP is present in rib_db (as destination)
    conn = sqlite3.connect(RIB_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT router, destination, interface FROM rib WHERE destination LIKE ?", (f"%{ip}%",))
    rib_rows = cur.fetchall()
    conn.close()
    if not rib_rows:
        return {"found": False, "ip": ip, "msg": f"IP {ip} not found in RIB."}
    # 2. Find router name (generic) and interface from inip.db
    conn = sqlite3.connect(INIP_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT router_name, interface FROM inip WHERE ip = ?", (ip,))
    inip_row = cur.fetchone()
    conn.close()
    if not inip_row:
        return {"found": False, "ip": ip, "msg": f"IP {ip} found in RIB but not in INIP."}
    router_name, interface = inip_row
    # 3. Get vendor using NETCONF (use router IP from rib_db)
    # Use the first router IP found in rib_db for this IP
    router_ip = rib_rows[0][0]
    hostname, version, vendor, status = get_device_info(router_ip, NETCONF_PORT, NETCONF_USERNAME, NETCONF_PASSWORD)
    return {
        "found": True,
        "ip": ip,
        "router_name": router_name,
        "interface": interface,
        "router_ip": router_ip,
        "vendor": vendor,
        "hostname": hostname,
        "version": version,
        "status": status
    }

def find_source_and_dest_info(src_ip, dst_ip):
    src_info = find_ip_info(src_ip)
    dst_info = find_ip_info(dst_ip)
    return {"source": src_info, "destination": dst_info} 