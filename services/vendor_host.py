"""
services/vendor_host.py
----------------------
Vendor-agnostic device information fetcher for network automation web app.
Provides functions to detect vendor, fetch hostname, software version, and status using NETCONF.
Supports Cisco, Juniper, Arista, and can be extended for other vendors.
"""

import socket
from ncclient import manager
from ncclient.xml_ import to_ele
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET

def is_port_open(host, port, timeout=2):
    """
    Check if a TCP port is open on a given host.
    Args:
        host (str): IP address or hostname.
        port (int): TCP port number.
        timeout (int): Timeout in seconds.
    Returns:
        bool: True if port is open, False otherwise.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def extract_vendor_name(text):
    """
    Extract vendor name from a capability string or namespace.
    Args:
        text (str): Capability or namespace string.
    Returns:
        str or None: Vendor name if detected, else None.
    """
    if not text:
        return None
    text = text.lower()
    if "cisco" in text:
        return "Cisco"
    elif "juniper" in text:
        return "Juniper"
    elif "nokia" in text or "alcatel" in text:
        return "Nokia"
    elif "huawei" in text:
        return "Huawei"
    elif "arista" in text:
        return "Arista"
    return None

def get_device_info(host, port, username, password):
    """
    Connect to a device via NETCONF and fetch hostname, software version, vendor, and status.
    Supports Cisco, Juniper, Arista. Extend for more vendors as needed.
    Args:
        host (str): Device IP address.
        port (int): NETCONF port.
        username (str): NETCONF username.
        password (str): NETCONF password.
    Returns:
        tuple: (hostname, software_version, vendor, status)
    """
    if not is_port_open(host, port):
        return "Unknown", "Unknown", "Unknown", "Not Enabled (No NETCONF)"
    try:
        with manager.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=10
        ) as m:
            print(f"\nDebug: Connected to {host}")
            print("Debug: Server capabilities:")
            for cap in m.server_capabilities:
                print(f"  {cap}")

            hostname = "Unknown"
            vendor = "Unknown"
            software_version = "Unknown"

            # Detect vendor first to use vendor-specific queries
            for capability in m.server_capabilities:
                if "cisco" in capability.lower():
                    vendor = "Cisco"
                    break
                elif "juniper" in capability.lower():
                    vendor = "Juniper"
                    break
                elif "arista" in capability.lower():
                    vendor = "Arista"
                    break

            print(f"\nDebug: Detected vendor: {vendor}")

            if vendor == "Cisco":
                print("\nDebug: Trying Cisco IOS-XE hostname and version...")
                filter_str = '''
                    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                        <version/>
                        <hostname/>
                    </native>
                '''
                reply = m.get(filter=('subtree', filter_str))
                print(f"Debug: Cisco reply XML:\n{reply.xml}")
                
                if reply is not None:
                    native = reply.data.find(".//{http://cisco.com/ns/yang/Cisco-IOS-XE-native}native")
                    if native is not None:
                        hostname_elem = native.find(".//{http://cisco.com/ns/yang/Cisco-IOS-XE-native}hostname")
                        version_elem = native.find(".//{http://cisco.com/ns/yang/Cisco-IOS-XE-native}version")
                        
                        if hostname_elem is not None and hostname_elem.text:
                            hostname = hostname_elem.text
                        if version_elem is not None and version_elem.text:
                            software_version = version_elem.text

            elif vendor == "Juniper":
                print("\nDebug: Trying Juniper configuration...")
                try:
                    # First try to get hostname using configuration data
                    hostname_filter = '''
                        <configuration xmlns="http://xml.juniper.net/xnm/1.1/xnm">
                            <system>
                                <host-name/>
                            </system>
                        </configuration>
                    '''
                    reply = m.get_config(source='running', filter=('subtree', hostname_filter))
                    print(f"Debug: Juniper hostname reply XML:\n{reply.xml}")
                    
                    if reply is not None:
                        system = reply.data.find(".//system")
                        if system is not None:
                            hostname_elem = system.find(".//host-name")
                            if hostname_elem is not None and hostname_elem.text:
                                hostname = hostname_elem.text
                    
                    # Then try to get version using get-software-information RPC
                    version_rpc = '''
                        <get-software-information>
                            <brief/>
                        </get-software-information>
                    '''
                    reply = m.rpc(to_ele(version_rpc))
                    print(f"Debug: Juniper version reply XML:\n{reply.xml}")
                    
                    if reply is not None:
                        # Parse the version information from the XML string
                        reply_str = reply.xml
                        if "<junos-version>" in reply_str:
                            start = reply_str.find("<junos-version>") + len("<junos-version>")
                            end = reply_str.find("</junos-version>")
                            if start > -1 and end > -1:
                                software_version = reply_str[start:end].strip()
                
                except Exception as e:
                    print(f"Debug: Juniper query failed: {str(e)}")

            elif vendor == "Arista":
                print("\nDebug: Trying Arista configuration...")
                try:
                    system_filter = '''
                        <system xmlns="http://openconfig.net/yang/system">
                            <state>
                                <hostname/>
                                <software-version/>
                            </state>
                        </system>
                    '''
                    reply = m.get(filter=('subtree', system_filter))
                    print(f"Debug: Arista system reply XML:\n{reply.xml}")
                    
                    if reply is not None:
                        system = reply.data.find(".//{http://openconfig.net/yang/system}state")
                        if system is not None:
                            hostname_elem = system.find(".//{http://openconfig.net/yang/system}hostname")
                            version_elem = system.find(".//{http://openconfig.net/yang/system}software-version")
                            
                            if hostname_elem is not None and hostname_elem.text:
                                hostname = hostname_elem.text
                            if version_elem is not None and version_elem.text:
                                software_version = version_elem.text
                except Exception as e:
                    print(f"Debug: Arista query failed: {str(e)}")

            status = "Enabled and Connected" if hostname != "Unknown" else "Enabled (Hostname Unavailable)"
            print(f"\nDebug: Final results for {host}:")
            print(f"  Hostname: {hostname}")
            print(f"  Software Version: {software_version}")
            print(f"  Vendor: {vendor}")
            print(f"  Status: {status}")
            
            return hostname, software_version, vendor, status

    except Exception as e:
        print(f"Error connecting to {host}: {str(e)}")
        return "Unknown", "Unknown", "Unknown", f"Error: {str(e)}" 