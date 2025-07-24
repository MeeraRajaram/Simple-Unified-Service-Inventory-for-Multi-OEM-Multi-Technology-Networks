"""
services/netconf_service.py
--------------------------
Network automation backend module for NETCONF-based interface and protocol discovery.
Provides functions to fetch interface details and enabled protocols from routers using NETCONF.
Designed for use in a modular Flask-based network automation web app.
"""

from services.vendor_host import get_device_info
from ncclient import manager
import xml.etree.ElementTree as ET
from services.ports_protocols import get_ports_and_protocols

# TODO: Replace print statements with logging for production/IEEE quality

def extract_interface_details(xml_data, ns):
    """
    Parse XML data to extract interface names and status.

    Args:
        xml_data (str): NETCONF XML response as string.
        ns (dict): Namespace mapping for XML parsing.
    Returns:
        list: List of interface names with status (e.g., ['GigabitEthernet1 (Up)'])
    """
    ports = []
    try:
        root = ET.fromstring(xml_data)
        for iface in root.findall(".//if:interface", ns):
            name = iface.find("if:name", ns)
            enabled = iface.find("if:enabled", ns)
            if name is not None:
                status = "Up" if (enabled is not None and enabled.text == 'true') else "Down"
                ports.append(f"{name.text} ({status})")
    except Exception:
        pass
    return ports if ports else ["Unknown"]

def extract_enabled_protocols(capabilities):
    """
    Parse NETCONF server capabilities to detect enabled protocols.

    Args:
        capabilities (iterable): NETCONF server capabilities.
    Returns:
        list: List of detected protocol names (e.g., ['NETCONF', 'BGP'])
    """
    protocols = set()
    for cap in capabilities:
        lcap = cap.lower()
        if "netconf" in lcap:
            protocols.add("NETCONF")
        if "openconfig" in lcap:
            protocols.add("OpenConfig")
        if "bgp" in lcap:
            protocols.add("BGP")
        if "ospf" in lcap:
            protocols.add("OSPF")
        if "lldp" in lcap:
            protocols.add("LLDP")
        if "routing" in lcap:
            protocols.add("Routing")
        if "yang" in lcap:
            protocols.add("YANG")
    return list(protocols) if protocols else ["Unknown"]

def get_ports_and_protocols(host, port, username, password):
    """
    Connect to a router via NETCONF and fetch interface and protocol information.

    Args:
        host (str): Router IP address.
        port (int): NETCONF port (default: 830).
        username (str): NETCONF username.
        password (str): NETCONF password.
    Returns:
        tuple: (list of interfaces, list of protocols)
    """
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
            # First try standard IETF interfaces
            ports = []
            iface_filter = """
            <filter>
              <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                <interface/>
              </interfaces>
            </filter>
            """
            try:
                iface_reply = m.get(iface_filter).data_xml
                ports = extract_interface_details(
                    iface_reply, {"if": "urn:ietf:params:xml:ns:yang:ietf-interfaces"}
                )
            except Exception:
                ports = ["Unknown"]

            # Detect protocols from capabilities
            protocols = extract_enabled_protocols(m.server_capabilities)

            return ports, protocols

    except Exception as e:
        print(f"❌ NETCONF Error on {host}: {e}")
        return ["Unknown"], ["Unknown"]

def check_netconf_for_ips(ip_cred_list):
    """
    For a list of IPs and credentials, check NETCONF connectivity and fetch device/interface/protocol info.

    Args:
        ip_cred_list (list): List of dicts with 'ip', 'username', 'password'.
    Returns:
        list: List of dicts with device and protocol/interface info.
    """
    results = []
    for entry in ip_cred_list:
        ip = entry['ip']
        username = entry['username']
        password = entry['password']
        hostname, software_version, vendor, netconf_status = get_device_info(ip, 830, username, password)
        ports, protocols = get_ports_and_protocols(ip, 830, username, password) if netconf_status.startswith('Enabled') else ([], [])
        results.append({
            'hostname': hostname or 'Unknown',
            'software_version': software_version or 'Unknown',
            'ip': ip,
            'vendor': vendor or 'Unknown',
            'username': username,
            'password': password,
            'netconf_status': netconf_status,
            'protocols': ', '.join(protocols) if protocols else 'Unknown',
            'ports': ', '.join(ports) if ports else 'Unknown'
        })
    return results 