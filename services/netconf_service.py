import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../day17/modules')))
from services.vendor_host import get_device_info
from ncclient import manager
import xml.etree.ElementTree as ET
from services.ports_protocols import get_ports_and_protocols

def extract_interface_details(xml_data, ns):
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