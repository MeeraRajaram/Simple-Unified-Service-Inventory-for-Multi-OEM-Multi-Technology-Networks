import xml.etree.ElementTree as ET
from prettytable import PrettyTable

def get_physical_inventory(m):
    """Get physical inventory with accurate status using device hardware operational data"""
    try:
        # Initialize table
        table = PrettyTable(["Interface", "IP Address", "Subnet Mask", "Status", "Capacity", "Usage"])
        
        # Get interface IP configuration
        ip_filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <interface>
              <GigabitEthernet>
                <name/>
                <ip>
                  <address>
                    <primary>
                      <address/>
                      <mask/>
                    </primary>
                  </address>
                </ip>
              </GigabitEthernet>
            </interface>
          </native>
        </filter>
        '''
        ip_result = m.get_config(source='running', filter=ip_filter)
        ip_root = ET.fromstring(ip_result.xml)
        ip_ns = {'native': 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
        
        # Get interface status from device hardware operational data
        status_filter = '''
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <device-hardware-data xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-device-hardware-oper">
            <device-hardware>
              <device-inventory>
                <hw-type>port</hw-type>
                <hw-dev-index/>
                <version/>
                <part-number/>
                <serial-number/>
                <hw-description/>
                <hw-status>
                  <hw-status-info>ok</hw-status-info>
                </hw-status>
                <hw-oper-state/>
              </device-inventory>
            </device-hardware>
          </device-hardware-data>
        </filter>
        '''
        status_result = m.get(filter=status_filter)
        status_root = ET.fromstring(status_result.xml)
        status_ns = {'hw': 'http://cisco.com/ns/yang/Cisco-IOS-XE-device-hardware-oper'}
        
        # Create a status mapping dictionary
        status_map = {}
        for inv in status_root.findall(".//hw:device-inventory", namespaces=status_ns):
            hw_desc = inv.find("hw:hw-description", namespaces=status_ns)
            state = inv.find("hw:hw-oper-state", namespaces=status_ns)
            if hw_desc is not None and state is not None:
                # Extract interface name from description (e.g., "GigabitEthernet0/1")
                if "GigabitEthernet" in hw_desc.text:
                    # Normalize interface name (remove any extra spaces or prefixes)
                    intf_name = "GigabitEthernet" + hw_desc.text.split("GigabitEthernet")[-1].split()[0]
                    status_map[intf_name] = state.text.lower()  # up/down
        
        # Process all GigabitEthernet interfaces
        interfaces = ip_root.findall(".//native:interface/native:GigabitEthernet", namespaces=ip_ns)
        for intf in interfaces:
            name = intf.find("native:name", namespaces=ip_ns)
            if name is not None:
                interface_name = f"GigabitEthernet{name.text}"
                
                # Get IP information
                ip_address = "N/A"
                subnet_mask = "N/A"
                ip_elem = intf.find(".//native:primary/native:address", namespaces=ip_ns)
                mask_elem = intf.find(".//native:primary/native:mask", namespaces=ip_ns)
                if ip_elem is not None and mask_elem is not None:
                    ip_address = ip_elem.text
                    subnet_mask = mask_elem.text
                
                # Get interface status from our mapping
                status = status_map.get(interface_name, "down")
                
                # Determine capacity and usage
                capacity = "1G"
                usage = "Used" if ip_address != "N/A" else "Free"
                
                table.add_row([
                    interface_name,
                    ip_address,
                    subnet_mask,
                    status,
                    capacity,
                    usage
                ])
        
        return table
        
    except Exception as e:
        print(f"⚠️ Physical inventory query failed: {str(e)}")
        return None