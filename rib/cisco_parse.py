from lxml import etree
from rib.db_utils import rib_db_manage

def parse_rib_xml(rib_xml, router_name, router_ip):
    routes = []
    loopback_ip = ''
    try:
        root = etree.fromstring(rib_xml.encode())
        ns = {'rt': 'urn:ietf:params:xml:ns:yang:ietf-routing'}
        # First pass: find the loopback IP (first /32 route with Loopback interface)
        for route in root.xpath('.//rt:route', namespaces=ns):
            destination = route.findtext('rt:destination-prefix', namespaces=ns)
            interface = route.findtext('rt:next-hop/rt:outgoing-interface', namespaces=ns)
            if destination and destination.endswith('/32') and interface and any(term.lower() in interface.lower() for term in ['Loopback', 'Lo', 'Lb']):
                loopback_ip = destination.replace('/32', '')
                break
        # Second pass: process all routes
        for route in root.xpath('.//rt:route', namespaces=ns):
            destination = route.findtext('rt:destination-prefix', namespaces=ns)
            protocol = route.findtext('rt:source-protocol', namespaces=ns)
            interface = route.findtext('rt:next-hop/rt:outgoing-interface', namespaces=ns)
            next_hop = route.findtext('rt:next-hop/rt:next-hop-address', namespaces=ns)
            # Skip routes with interface 'LIIN0'
            if interface and interface.strip().upper() == 'LIIN0':
                continue
            # Protocol mapping
            protocol_map = {
                'direct': 'Connected',
                'local': 'Local',
                'static': 'Static',
                'ospfv2': 'OSPF',
                'ospf': 'OSPF',
            }
            if protocol and ':' in protocol:
                protocol = protocol.split(':')[-1]
            protocol_display = protocol_map.get(protocol, protocol.capitalize() if protocol else '')
            # Next hop mapping
            if not next_hop or next_hop == '0.0.0.0':
                next_hop_display = 'Directly connected'
            else:
                next_hop_display = next_hop
            # Clean up interface name (remove subinterface if present)
            if interface and '.' in interface:
                interface = interface.split('.')[0]
            routes.append({
                'Router': router_name,
                'Loopback IP': loopback_ip,
                'Protocol': protocol_display,
                'Destination': destination or '',
                'Interface': interface or '',
                'Next Hop': next_hop_display
            })
            rib_db_manage.add_entry(router_name, loopback_ip, protocol_display, destination or '', interface or '', next_hop_display)
        return routes
    except Exception as e:
        print(f"Error parsing RIB XML: {e}")
        return []
