import xml.etree.ElementTree as ET
from prettytable import PrettyTable

def get_device_info(m):
    """Get Cisco device information including hostname and loopback IP"""
    try:
        filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <hostname/>
            <interface>
              <Loopback/>
            </interface>
          </native>
        </filter>
        '''
        result = m.get_config(source='running', filter=filter)
        root = ET.fromstring(result.xml)
        ns = {'native': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
        
        hostname = root.find(".//native:hostname", namespaces=ns)
        loopbacks = root.findall(".//native:Loopback", namespaces=ns)
        
        loopback_ip = "None"
        for loopback in loopbacks:
            ip = loopback.find("native:ip/native:address/native:primary/native:address", namespaces=ns)
            if ip is not None:
                loopback_ip = ip.text
                break
        
        return {
            'hostname': hostname.text if hostname is not None else 'Unknown',
            'loopback': loopback_ip
        }
    except Exception as e:
        print(f"⚠️ Could not retrieve device information: {str(e)}")
        return {
            'hostname': 'Unknown',
            'loopback': 'Unknown'
        }

def get_vrf_info(m):
    """Get VRF information for Cisco devices"""
    try:
        filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <vrf>
              <definition>
                <name/>
                <rd/>
                <address-family>
                  <ipv4/>
                  <ipv6/>
                </address-family>
              </definition>
            </vrf>
            <interface>
              <GigabitEthernet/>
              <Loopback/>
              <Tunnel/>
            </interface>
          </native>
        </filter>
        '''
        result = m.get_config(source='running', filter=filter)

        root = ET.fromstring(result.xml)
        ns = {
            'native': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'
        }

        vrfs = root.findall(".//native:vrf/native:definition", namespaces=ns)
        if not vrfs:
            return None

        # Collect all interfaces and their VRF assignments
        vrf_interfaces = {}
        for intf_type in ['GigabitEthernet', 'Loopback', 'Tunnel']:
            interfaces = root.findall(f".//native:interface/native:{intf_type}", namespaces=ns)
            for intf in interfaces:
                name = intf.find("native:name", namespaces=ns)
                vrf = intf.find("native:vrf/native:forwarding", namespaces=ns)
                if vrf is not None and name is not None:
                    if vrf.text not in vrf_interfaces:
                        vrf_interfaces[vrf.text] = []
                    vrf_interfaces[vrf.text].append(f"{intf_type}{name.text}")

        table = PrettyTable(["VRF Name", "RD", "IPv4", "IPv6", "Interfaces"])
        for vrf in vrfs:
            name = vrf.find("native:name", namespaces=ns)
            rd = vrf.find("native:rd", namespaces=ns)
            ipv4 = vrf.find("native:address-family/native:ipv4", namespaces=ns)
            ipv6 = vrf.find("native:address-family/native:ipv6", namespaces=ns)
            interfaces = vrf_interfaces.get(name.text if name is not None else "", [])
            interface_list = ", ".join(interfaces) if interfaces else "None"

            table.add_row([
                name.text if name is not None else "N/A",
                rd.text if rd is not None else "N/A",
                "Enabled" if ipv4 is not None else "Disabled",
                "Enabled" if ipv6 is not None else "Disabled",
                interface_list
            ])
        return table

    except Exception as e:
        print(f"⚠️ VRF query failed: {str(e)}")
        return None

def get_vlan_info(m):
    """Get VLAN information for Cisco devices"""
    try:
        filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <vlan>
              <vlan-list/>
            </vlan>
          </native>
        </filter>
        '''
        result = m.get_config(source='running', filter=filter)

        root = ET.fromstring(result.xml)
        ns = {'native': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
        
        vlans = root.findall(".//native:vlan/native:vlan-list", namespaces=ns)
        if not vlans:
            return None
            
        table = PrettyTable(["VLAN ID", "Name", "Status"])
        for vlan in vlans:
            vlan_id = vlan.find("native:id", namespaces=ns)
            name = vlan.find("native:name", namespaces=ns)
            status = vlan.find("native:shutdown", namespaces=ns)
            
            table.add_row([
                vlan_id.text if vlan_id is not None else "N/A",
                name.text if name is not None else "N/A",
                "Active" if status is None or status.text == "false" else "Inactive"
            ])
        return table
        
    except Exception as e:
        print(f"⚠️ VLAN query failed: {str(e)}")
        return None

def get_mpls_info(m):
    """Get MPLS information for Cisco devices"""
    try:
        filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <mpls xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-mpls">
            <lsr-id/>
            <ldp>
              <router-id/>
              <discovery>
                <interfaces/>
              </discovery>
            </ldp>
          </mpls>
        </filter>
        '''
        result = m.get_config(source='running', filter=filter)

        root = ET.fromstring(result.xml)
        ns = {'mpls': 'http://cisco.com/ns/yang/Cisco-IOS-XE-mpls'}
        
        lsr_id = root.find(".//mpls:lsr-id", namespaces=ns)
        ldp_rid = root.find(".//mpls:ldp/mpls:router-id", namespaces=ns)
        interfaces = root.findall(".//mpls:ldp/mpls:discovery/mpls:interfaces", namespaces=ns)
        
        table = PrettyTable(["MPLS LSR ID", "LDP Router ID", "Interfaces"])
        intf_list = ", ".join([intf.text for intf in interfaces if intf.text])
        
        table.add_row([
            lsr_id.text if lsr_id is not None else "N/A",
            ldp_rid.text if ldp_rid is not None else "N/A",
            intf_list if intf_list else "N/A"
        ])
        return table
        
    except Exception as e:
        print(f"⚠️ MPLS query failed: {str(e)}")
        return None

def get_l2vpn_info(m):
    """Get L2VPN information for Cisco devices"""
    try:
        filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <l2vpn xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-l2vpn">
            <xconnect>
              <groups/>
            </xconnect>
          </l2vpn>
        </filter>
        '''
        result = m.get_config(source='running', filter=filter)

        root = ET.fromstring(result.xml)
        ns = {'l2vpn': 'http://cisco.com/ns/yang/Cisco-IOS-XE-l2vpn'}
        
        groups = root.findall(".//l2vpn:xconnect/l2vpn:groups", namespaces=ns)
        if not groups:
            return None
            
        table = PrettyTable(["Group Name", "Interface", "Target"])
        for group in groups:
            name = group.find("l2vpn:name", namespaces=ns)
            interface = group.find("l2vpn:p2p/l2vpn:interface", namespaces=ns)
            target = group.find("l2vpn:p2p/l2vpn:neighbor/l2vpn:address", namespaces=ns)
            table.add_row([
                name.text if name is not None else "N/A",
                interface.text if interface is not None else "N/A",
                target.text if target is not None else "N/A"
            ])
        return table
        
    except Exception as e:
        print(f"⚠️ L2VPN query failed: {str(e)}")
        return None

def get_l3vpn_info(m):
    """Get L3VPN information for Cisco devices"""
    try:
        filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <vrf>
              <definition xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-vrf">
                <name/>
                <rd/>
                <address-family>
                  <ipv4>
                    <route-target>
                      <import/>
                      <export/>
                    </route-target>
                  </ipv4>
                </address-family>
              </definition>
            </vrf>
            <router>
              <bgp xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-bgp">
                <address-family>
                  <with-vrf>
                    <ipv4>
                      <vpn/>
                    </ipv4>
                  </with-vrf>
                </address-family>
              </bgp>
            </router>
          </native>
        </filter>
        '''
        result = m.get_config(source='running', filter=filter)

        root = ET.fromstring(result.xml)
        ns = {
            'native': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native',
            'vrf': 'http://cisco.com/ns/yang/Cisco-IOS-XE-vrf',
            'bgp': 'http://cisco.com/ns/yang/Cisco-IOS-XE-bgp'
        }
        
        # Check for VPNv4 BGP configuration
        vpnv4 = root.find(".//native:router/bgp:bgp/bgp:address-family/bgp:with-vrf/bgp:ipv4/bgp:vpn", namespaces=ns)
        if vpnv4 is None:
            return None
            
        # Get VRF configurations
        table = PrettyTable(["VRF", "RD", "Import RT", "Export RT"])
        vrfs = root.findall(".//native:vrf/vrf:definition", namespaces=ns)
        
        for vrf in vrfs:
            name = vrf.find("vrf:name", namespaces=ns)
            rd = vrf.find("vrf:rd", namespaces=ns)
            import_rt = vrf.find("vrf:address-family/vrf:ipv4/vrf:route-target/vrf:import", namespaces=ns)
            export_rt = vrf.find("vrf:address-family/vrf:ipv4/vrf:route-target/vrf:export", namespaces=ns)
            
            table.add_row([
                name.text if name is not None else "N/A",
                rd.text if rd is not None else "N/A",
                import_rt.text if import_rt is not None else "N/A",
                export_rt.text if export_rt is not None else "N/A"
            ])
        
        return table if vrfs else None
        
    except Exception as e:
        print(f"⚠️ L3VPN query failed: {str(e)}")
        return None

def get_mvpn_info(m):
    """Get MVPN information for Cisco devices"""
    try:
        filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <mpls xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-mpls">
            <mvpn/>
          </mpls>
        </filter>
        '''
        result = m.get_config(source='running', filter=filter)

        root = ET.fromstring(result.xml)
        ns = {'mpls': 'http://cisco.com/ns/yang/Cisco-IOS-XE-mpls'}
        
        mvpn = root.find(".//mpls:mvpn", namespaces=ns)
        if mvpn is None:
            return None
            
        table = PrettyTable(["MVPN Instance", "MDT Group", "Status"])
        instance = mvpn.find("mpls:instance", namespaces=ns)
        mdt = mvpn.find("mpls:mdt", namespaces=ns)
        status = mvpn.find("mpls:status", namespaces=ns)
        
        table.add_row([
            instance.text if instance is not None else "N/A",
            mdt.text if mdt is not None else "N/A",
            status.text if status is not None else "N/A"
        ])
        return table
        
    except Exception as e:
        print(f"⚠️ MVPN query failed: {str(e)}")
        return None

def discover_services(m):
    """Discover all services on Cisco device"""
    # Get basic device info
    device_info = get_device_info(m)
    print(f"\nDevice Information:")
    print(f"Hostname: {device_info['hostname']}")
    print(f"Loopback IP: {device_info['loopback']}")
    
    # VRF
    vrf_table = get_vrf_info(m)
    if vrf_table:
        print("\nVRF Configuration:")
        print(vrf_table)
    else:
        print("\nNo VRF configurations found")
    
    # MPLS
    mpls_table = get_mpls_info(m)
    if mpls_table:
        print("\nMPLS Configuration:")
        print(mpls_table)
    else:
        print("\nNo MPLS configurations found")
    
    # VLAN
    vlan_table = get_vlan_info(m)
    if vlan_table:
        print("\nVLAN Configuration:")
        print(vlan_table)
    else:
        print("\nNo VLAN configurations found")
    
    # L2VPN
    l2vpn_table = get_l2vpn_info(m)
    if l2vpn_table:
        print("\nL2VPN Configuration:")
        print(l2vpn_table)
    else:
        print("\nNo L2VPN configurations found")
    
    # L3VPN
    l3vpn_table = get_l3vpn_info(m)
    if l3vpn_table:
        print("\nL3VPN Configuration:")
        print(l3vpn_table)
    else:
        print("\nNo L3VPN configurations found")
    
    # MVPN (only if MPLS is enabled)
    if mpls_table:
        mvpn_table = get_mvpn_info(m)
        if mvpn_table:
            print("\nMVPN Configuration:")
            print(mvpn_table)
        else:
            print("\nNo MVPN configurations found")