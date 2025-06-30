from ncclient import manager
import xml.etree.ElementTree as ET

def extract_interface_details(xml_data, ns_tag):
    ports = []
    try:
        root = ET.fromstring(xml_data)
        for iface in root.findall(f".//{ns_tag}interface"):
            name = iface.find(f"{ns_tag}name")
            enabled = iface.find(f"{ns_tag}enabled")
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

            # Try standard IETF interfaces first
            ports = []
            try:
                ietf_filter = """
                <filter>
                  <interfaces xmlns="urn:ietf:params:xml:ns:yang:ietf-interfaces">
                    <interface/>
                  </interfaces>
                </filter>
                """
                iface_reply = m.get(ietf_filter).data_xml
                ports = extract_interface_details(iface_reply, "{urn:ietf:params:xml:ns:yang:ietf-interfaces}")
            except:
                ports = []

            # Try Cisco fallback if needed
            if not ports or ports == ["Unknown"]:
                try:
                    cisco_filter = """
                    <filter>
                      <interfaces xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper">
                        <interface/>
                      </interfaces>
                    </filter>
                    """
                    iface_reply = m.get(cisco_filter).data_xml
                    ports = extract_interface_details(iface_reply, "{http://cisco.com/ns/yang/Cisco-IOS-XE-interfaces-oper}")
                except:
                    pass

            # Try Juniper fallback if needed
            if not ports or ports == ["Unknown"]:
                try:
                    juniper_filter = """
                    <filter>
                      <interface-information xmlns="http://xml.juniper.net/junos/18.4R1/junos-interface">
                        <physical-interface/>
                      </interface-information>
                    </filter>
                    """
                    iface_reply = m.get(juniper_filter).data_xml
                    root = ET.fromstring(iface_reply)
                    ports = []
                    for pi in root.findall(".//{http://xml.juniper.net/junos/18.4R1/junos-interface}physical-interface"):
                        name_elem = pi.find("{http://xml.juniper.net/junos/18.4R1/junos-interface}name")
                        admin_status = pi.find("{http://xml.juniper.net/junos/18.4R1/junos-interface}admin-status")
                        if name_elem is not None:
                            status = "Up" if admin_status is not None and admin_status.text.lower() == "up" else "Down"
                            ports.append(f"{name_elem.text} ({status})")
                    if not ports:
                        ports = ["Unknown"]
                except:
                    ports = ["Unknown"]

            # Get protocols
            protocols = extract_enabled_protocols(m.server_capabilities)

            return ports, protocols

    except Exception as e:
        print(f"❌ NETCONF Error on {host}: {e}")
        return ["Unknown"], ["Unknown"] 