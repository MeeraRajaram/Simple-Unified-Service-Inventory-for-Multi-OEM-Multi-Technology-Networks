"""
l3vpn/main.py
-------------
Standalone VRF push script for network automation web app.
Reads VRF configuration data from vrf.db and pushes VRF config to each router using NETCONF.
"""

import sqlite3
import os
from ncclient import manager
from ncclient.transport.errors import AuthenticationError

VRF_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'vrf.db')

# Helper to build VRF config XML
def build_vrf_config(vrf_name, rd, rt, description):
    """
    Build the VRF configuration XML for Cisco IOS XE routers.

    Args:
        vrf_name (str): VRF name.
        rd (str): Route Distinguisher.
        rt (str): Route Target(s), space-separated direction,target pairs.
        description (str): VRF description.
    Returns:
        str: XML string for VRF configuration.
    Raises:
        ValueError: If RT entry format is invalid.
    """
    config = f"""
    <config>
        <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <vrf>
                <definition>
                    <name>{vrf_name}</name>
                    <rd>{rd}</rd>
                    {f'<description>{description}</description>' if description else ''}
    """
    for rt_entry in rt.split():
        if ',' not in rt_entry:
            raise ValueError(f"Invalid RT entry: '{rt_entry}'. Format must be direction,target (e.g. import,65000:1)")
        direction, target = rt_entry.split(',', 1)
        config += f"""
                    <route-target>
                        <{direction}>
                            <asn-ip>{target}</asn-ip>
                        </{direction}>
                    </route-target>
        """
    config += """
                </definition>
            </vrf>
        </native>
    </config>
    """
    return config

if __name__ == "__main__":
    """
    Main entry point: Reads VRF data from vrf.db and pushes configuration to each router using NETCONF.
    """
    conn = sqlite3.connect(VRF_DB_PATH)
    c = conn.cursor()
    c.execute('SELECT router_name, router_loopback_ip, vrf_name, rd, rt, description, netconf_username, netconf_password FROM vrf')
    rows = c.fetchall()
    conn.close()
    for row in rows:
        router_name, host, vrf_name, rd, rt, description, username, password = row
        print(f"Connecting to {router_name} ({host})...")
        try:
            with manager.connect(
                host=host,
                port=830,
                username=username,
                password=password,
                hostkey_verify=False
            ) as m:
                config_xml = build_vrf_config(vrf_name, rd, rt, description)
                m.edit_config(target='running', config=config_xml)
                print(f"[SUCCESS] VRF pushed to {router_name} ({host})")
        except AuthenticationError:
            print(f"[FAIL] Authentication failed for {router_name} ({host})")
        except Exception as e:
            print(f"[FAIL] Error for {router_name} ({host}): {e}") 