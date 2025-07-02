import xml.etree.ElementTree as ET
from prettytable import PrettyTable

def get_physical_inventory(m):
    """Get physical inventory for Arista devices with multiple fallback methods"""
    try:
        # Method 1: Try OpenConfig model
        try:
            print("\nAttempting OpenConfig method...")
            filter = '''
            <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
              <components xmlns="http://openconfig.net/yang/platform"/>
              <interfaces xmlns="http://openconfig.net/yang/interfaces"/>
            </filter>
            '''
            result = m.get(filter=filter)
            
            root = ET.fromstring(result.xml)
            ns = {
                'oc-platform': 'http://openconfig.net/yang/platform',
                'oc-if': 'http://openconfig.net/yang/interfaces',
                'oc-eth': 'http://openconfig.net/yang/interfaces/ethernet',
                'oc-ip': 'http://openconfig.net/yang/interfaces/ip'
            }

            table = PrettyTable(["Interface", "Type", "Status", "Speed", "IP Address", "Description"])
            
            # Get interface information
            interfaces = root.findall(".//oc-if:interface", namespaces=ns)
            for intf in interfaces:
                name = intf.find("oc-if:name", namespaces=ns)
                if name is None or not name.text:
                    continue
                
                # Get operational status
                oper_status = intf.find(".//oc-if:state/oc-if:oper-status", namespaces=ns)
                admin_status = intf.find(".//oc-if:state/oc-if:admin-status", namespaces=ns)
                
                # Get speed information
                speed = intf.find(".//oc-eth:state/oc-eth:port-speed", namespaces=ns)
                negotiated_speed = intf.find(".//oc-eth:state/oc-eth:negotiated-port-speed", namespaces=ns)
                
                # Get IP address if available
                ip_address = ""
                ip_node = intf.find(".//oc-ip:address/oc-ip:ip", namespaces=ns)
                if ip_node is not None and ip_node.text:
                    ip_address = ip_node.text
                
                # Get description from hardware port if available
                description = ""
                hw_port = intf.find(".//oc-if:state/oc-platform:hardware-port", namespaces=ns)
                if hw_port is not None and hw_port.text:
                    # Try to find component with matching name for description
                    for comp in root.findall(".//oc-platform:component", namespaces=ns):
                        comp_name = comp.find("oc-platform:name", namespaces=ns)
                        if comp_name is not None and comp_name.text == hw_port.text:
                            desc = comp.find(".//oc-platform:state/oc-platform:description", namespaces=ns)
                            if desc is not None and desc.text:
                                description = desc.text
                            break
                
                # Determine status
                status = "unknown"
                if admin_status is not None and admin_status.text:
                    status = "admin down" if admin_status.text.lower() == "down" else oper_status.text.lower() if oper_status is not None else "unknown"
                
                # Determine speed
                speed_str = "N/A"
                if speed is not None and speed.text:
                    speed_str = speed.text.replace("SPEED_", "").replace("MB", "M").replace("GB", "G")
                elif negotiated_speed is not None and negotiated_speed.text:
                    speed_str = negotiated_speed.text.replace("SPEED_", "").replace("MB", "M").replace("GB", "G")
                
                # Determine interface type
                intf_type = "Other"
                if "Ethernet" in name.text:
                    intf_type = "Ethernet"
                elif "Management" in name.text:
                    intf_type = "Management"
                elif "Loopback" in name.text:
                    intf_type = "Loopback"
                
                table.add_row([
                    name.text,
                    intf_type,
                    status,
                    speed_str,
                    ip_address,
                    description
                ])
            
            if len(table._rows) > 0:
                return table
            
        except Exception as oc_error:
            print(f"OpenConfig method failed: {str(oc_error)}")

        # Method 2: Try Arista's native EOS model
        try:
            print("\nAttempting Arista EOS native method...")
            filter = '''
            <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
              <interfaces xmlns="http://arista.com/yang/arista-intf">
                <interface>
                  <name/>
                  <interfaceStatus>
                    <linkStatus/>
                  </interfaceStatus>
                  <bandwidth/>
                </interface>
              </interfaces>
            </filter>
            '''
            result = m.get(filter=filter)
            
            root = ET.fromstring(result.xml)
            ns = {'ar-intf': 'http://arista.com/yang/arista-intf'}

            table = PrettyTable(["Interface", "Status", "Speed"])
            
            interfaces = root.findall(".//ar-intf:interface", namespaces=ns)
            for intf in interfaces:
                name = intf.find("ar-intf:name", namespaces=ns)
                if name is None or not name.text:
                    continue
                
                # Try different possible locations for status
                status = (intf.find(".//ar-intf:interfaceStatus/ar-intf:linkStatus", namespaces=ns) or 
                          intf.find(".//ar-intf:linkStatus", namespaces=ns) or
                          intf.find(".//ar-intf:oper-status", namespaces=ns))
                
                bandwidth = intf.find("ar-intf:bandwidth", namespaces=ns)
                
                speed_str = "N/A"
                if bandwidth is not None and bandwidth.text:
                    try:
                        speed_mbps = int(bandwidth.text) / 1000000
                        speed_str = f"{int(speed_mbps)}M" if speed_mbps < 1000 else f"{int(speed_mbps/1000)}G"
                    except ValueError:
                        pass
                
                table.add_row([
                    name.text,
                    status.text.lower() if status is not None and status.text else "unknown",
                    speed_str
                ])
            
            if len(table._rows) > 0:
                return table
            
        except Exception as eos_error:
            print(f"Arista EOS native method failed: {str(eos_error)}")

        print("\nAll methods failed. No physical inventory information available.")
        return None

    except Exception as e:
        print(f"⚠️ All physical inventory methods failed: {str(e)}")
        return None