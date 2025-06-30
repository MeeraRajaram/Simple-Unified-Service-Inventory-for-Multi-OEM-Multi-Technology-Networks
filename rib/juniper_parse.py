from lxml import etree
from rib.db_utils import rib_db_manage
import sys

def parse_juniper_routing(xml_data, hostname='Juniper-Router'):
    """
    Parses Juniper routing XML into structured data
    Returns list of dictionaries with schema:
    Router | Loopback IP | Protocol | Destination | Interface | Next Hop
    Adds entries to rib_db_manage as well.
    """
    try:
        root = etree.fromstring(xml_data.encode())
        # Extract loopback IP (first /32 route in private range)
        loopback_ip = None
        for ip in root.xpath('//rt[starts-with(rt-destination, "192.168.") or starts-with(rt-destination, "10.")]/rt-destination/text()'):
            if ip.endswith('/32'):
                loopback_ip = ip.split('/')[0]
                break
        routes = []
        for rt in root.xpath('//rt'):
            destination = rt.xpath('rt-destination/text()')
            if not destination:
                continue
            destination = destination[0]
            for entry in rt.xpath('rt-entry'):
                protocol = entry.xpath('protocol-name/text()')
                protocol = protocol[0] if protocol else 'N/A'
                next_hop = entry.xpath('nh/to/text()')
                interface = entry.xpath('nh/via/text()')
                # Handle special cases
                if not next_hop:
                    if protocol.lower() == "local":
                        next_hop = ["Local"]
                    elif protocol.lower() == "direct":
                        next_hop = ["Direct"]
                    else:
                        next_hop = ["N/A"]
                if not interface:
                    interface = ["N/A"]
                route = {
                    'Router': hostname,
                    'Loopback IP': loopback_ip,
                    'Protocol': protocol,
                    'Destination': destination,
                    'Interface': interface[0],
                    'Next Hop': next_hop[0]
                }
                routes.append(route)
                rib_db_manage.add_entry(hostname, loopback_ip, protocol, destination, interface[0], next_hop[0])
        return routes
    except Exception as e:
        print(f"Error parsing XML: {str(e)}", file=sys.stderr)
        return []

def parse_juniper_rpc_xml(xml_data, hostname):
    root = etree.fromstring(xml_data.encode())
    routes = []
    # Find loopback IP (first /32 in private range)
    loopback_ip = None
    for rt in root.xpath('.//rt'):
        dest = rt.findtext('rt-destination')
        if dest and dest.endswith('/32') and (dest.startswith('192.168.') or dest.startswith('10.')):
            loopback_ip = dest.split('/')[0]
            break
    for rt in root.xpath('.//rt'):
        destination = rt.findtext('rt-destination')
        entry = rt.find('rt-entry')
        if entry is None or destination is None:
            continue
        protocol = entry.findtext('protocol-name', default='N/A')
        nh = entry.find('nh')
        if nh is not None:
            next_hop = nh.findtext('to') or nh.findtext('nh-local-interface') or 'N/A'
            interface = nh.findtext('via') or nh.findtext('nh-local-interface') or 'N/A'
        else:
            next_hop = 'N/A'
            interface = 'N/A'
        if protocol and protocol.lower() == 'local':
            next_hop = 'Local'
        elif protocol and protocol.lower() == 'direct':
            next_hop = 'Direct'
        route = {
            'Router': hostname,
            'Loopback IP': loopback_ip,
            'Protocol': protocol,
            'Destination': destination,
            'Interface': interface,
            'Next Hop': next_hop
        }
        routes.append(route)
        rib_db_manage.add_entry(hostname, loopback_ip, protocol, destination, interface, next_hop)
    return routes

if __name__ == "__main__":
    with open("juniper_rpc.xml") as f:
        xml_data = f.read()
    routes = parse_juniper_rpc_xml(xml_data, hostname="Juniper-Router")
    from tabulate import tabulate
    print(tabulate(routes, headers="keys", tablefmt="grid"))
