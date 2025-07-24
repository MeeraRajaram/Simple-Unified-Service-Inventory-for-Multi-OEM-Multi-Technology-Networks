"""
rib/arista_parse.py
-------------------
Arista RIB (Routing Information Base) XML parsing and database integration module for network automation web app.
Provides functions to retrieve, parse, and store interface and routing data from Arista EOS devices using OpenConfig YANG models.
"""

from lxml import etree
from rib.db_utils import rib_db_manage

def get_interface_ip_config(device):
    """
    Retrieve all interface IP configurations from an Arista device using NETCONF.

    Args:
        device (dict): NETCONF connection parameters for the device.
    Returns:
        str: XML string of interface configuration data.
    """
    from ncclient import manager
    with manager.connect(**device, timeout=10) as m:
        filter_xml = """
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <interfaces xmlns="http://openconfig.net/yang/interfaces">
            <interface/>
          </interfaces>
        </filter>
        """
        response = m.get(filter_xml)
        return etree.tostring(response.data, pretty_print=True).decode()

def get_rib_data(device):
    """
    Retrieve routing information base (RIB) data from an Arista device using NETCONF.

    Args:
        device (dict): NETCONF connection parameters for the device.
    Returns:
        str: XML string of RIB data.
    """
    from ncclient import manager
    with manager.connect(**device, timeout=10) as m:
        filter_xml = """
        <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <network-instances xmlns="http://openconfig.net/yang/network-instance">
            <network-instance>
              <name>default</name>
            </network-instance>
          </network-instances>
        </filter>
        """
        response = m.get(filter_xml)
        return etree.tostring(response.data, pretty_print=True).decode()

def parse_interface_data(xml_data):
    """
    Parse interface XML data to extract IPv4 and IPv6 addresses for each interface.

    Args:
        xml_data (str): XML string of interface data.
    Returns:
        dict: Mapping of interface names to their IPv4 and IPv6 addresses.
    """
    root = etree.fromstring(xml_data.encode())
    ns = {'oc-if': 'http://openconfig.net/yang/interfaces', 'oc-ip': 'http://openconfig.net/yang/interfaces/ip'}
    interfaces = {}
    for iface in root.xpath('//oc-if:interface', namespaces=ns):
        name = iface.xpath('oc-if:name/text()', namespaces=ns)
        if not name:
            continue
        name = name[0]
        interfaces[name] = {'ipv4': [], 'ipv6': []}
        # Get IPv4 addresses
        for ipv4 in iface.xpath('.//oc-ip:ipv4/oc-ip:addresses/oc-ip:address', namespaces=ns):
            ip = ipv4.xpath('oc-ip:ip/text()', namespaces=ns)
            prefix = ipv4.xpath('oc-ip:config/oc-ip:prefix-length/text()', namespaces=ns)
            if ip and prefix:
                interfaces[name]['ipv4'].append(f"{ip[0]}/{prefix[0]}")
        # Get IPv6 addresses
        for ipv6 in iface.xpath('.//oc-ip:ipv6/oc-ip:addresses/oc-ip:address', namespaces=ns):
            ip = ipv6.xpath('oc-ip:ip/text()', namespaces=ns)
            prefix = ipv6.xpath('oc-ip:config/oc-ip:prefix-length/text()', namespaces=ns)
            if ip and prefix:
                interfaces[name]['ipv6'].append(f"{ip[0]}/{prefix[0]}")
    return interfaces

def parse_routing_data(xml_data, interfaces, router_name, router_ip):
    """
    Parse routing XML data and combine with interface information to build a routing table.

    Args:
        xml_data (str): XML string of routing data.
        interfaces (dict): Mapping of interface names to IP addresses.
        router_name (str): Hostname of the router.
        router_ip (str): Management or loopback IP address of the router.
    Returns:
        list: List of route entries (dicts) with protocol, destination, interface, and next hop.
    """
    root = etree.fromstring(xml_data.encode())
    ns = {
        'oc-ni': 'http://openconfig.net/yang/network-instance',
        'oc-pol': 'http://openconfig.net/yang/policy-types',
        'oc-bgp': 'http://openconfig.net/yang/bgp',
        'oc-ospf': 'http://openconfig.net/yang/ospf'
    }
    routing_table = []
    # Get router hostname (for Router column)
    hostname = root.xpath('//oc-ni:config/oc-ni:name/text()', namespaces=ns)
    router_name = hostname[0] if hostname else router_name
    # Get loopback IP (assuming interface named Loopback0)
    loopback_ip = None
    if 'Loopback0' in interfaces and interfaces['Loopback0']['ipv4']:
        loopback_ip = interfaces['Loopback0']['ipv4'][0].split('/')[0]
    # 1. Static Routes
    for route in root.xpath('//oc-ni:static', namespaces=ns):
        prefix = route.xpath('oc-ni:prefix/text()', namespaces=ns)
        if not prefix:
            continue
        prefix = prefix[0]
        next_hops = route.xpath('.//oc-ni:next-hop', namespaces=ns)
        for nh in next_hops:
            next_hop = nh.xpath('oc-ni:config/oc-ni:next-hop/text()', namespaces=ns)
            interface = nh.xpath('oc-ni:interface-ref/oc-ni:config/oc-ni:interface/text()', namespaces=ns)
            route_entry = {
                'Router': router_name,
                'Loopback IP': loopback_ip,
                'Protocol': 'Static',
                'Destination': prefix,
                'Interface': interface[0] if interface else 'N/A',
                'Next Hop': next_hop[0] if next_hop else 'Direct'
            }
            routing_table.append(route_entry)
            rib_db_manage.add_entry(router_name, loopback_ip, 'Static', prefix, 
                                  interface[0] if interface else 'N/A', 
                                  next_hop[0] if next_hop else 'Direct')
    # 2. OSPF Routes
    for route in root.xpath('//oc-ni:protocols/oc-ni:protocol[oc-ni:identifier="oc-pol:OSPF"]/oc-ni:ospf/oc-ni:routes/oc-ni:route', namespaces=ns):
        prefix = route.xpath('oc-ni:prefix/text()', namespaces=ns)
        next_hop = route.xpath('oc-ni:next-hop/text()', namespaces=ns)
        outgoing_if = route.xpath('oc-ni:outgoing-interface/text()', namespaces=ns)
        if prefix and next_hop:
            route_entry = {
                'Router': router_name,
                'Loopback IP': loopback_ip,
                'Protocol': 'OSPF',
                'Destination': prefix[0],
                'Interface': outgoing_if[0] if outgoing_if else 'N/A',
                'Next Hop': next_hop[0]
            }
            routing_table.append(route_entry)
            rib_db_manage.add_entry(router_name, loopback_ip, 'OSPF', prefix[0], 
                                  outgoing_if[0] if outgoing_if else 'N/A', next_hop[0])
    # 3. BGP Routes
    for route in root.xpath('//oc-ni:protocols/oc-ni:protocol[oc-ni:identifier="oc-pol:BGP"]/oc-ni:bgp/oc-ni:rib/oc-ni:afi-safis/oc-ni:afi-safi/oc-ni:ipv4-unicast/oc-ni:routes/oc-ni:route', namespaces=ns):
        prefix = route.xpath('oc-ni:prefix/text()', namespaces=ns)
        next_hop = route.xpath('oc-ni:state/oc-ni:next-hop/text()', namespaces=ns)
        if prefix and next_hop:
            # Try to find the outgoing interface for this next hop
            outgoing_if = None
            for iface, ips in interfaces.items():
                for ip in ips['ipv4'] + ips['ipv6']:
                    if ip.startswith(next_hop[0]):
                        outgoing_if = iface
                        break
                if outgoing_if:
                    break
            route_entry = {
                'Router': router_name,
                'Loopback IP': loopback_ip,
                'Protocol': 'BGP',
                'Destination': prefix[0],
                'Interface': outgoing_if if outgoing_if else 'N/A',
                'Next Hop': next_hop[0]
            }
            routing_table.append(route_entry)
            rib_db_manage.add_entry(router_name, loopback_ip, 'BGP', prefix[0], 
                                  outgoing_if if outgoing_if else 'N/A', next_hop[0])
    return routing_table

def parse_rib_xml(rib_xml, router_name, router_ip):
    """
    Parse RIB XML from an Arista device and store parsed routes in the database using enhanced logic.

    Args:
        rib_xml (str): XML string containing RIB and interface data.
        router_name (str): Hostname of the router.
        router_ip (str): Management or loopback IP address of the router.
    Returns:
        list: List of parsed route entries (dicts) with protocol, destination, interface, and next hop.
    """
    routes = []
    loopback_ip = ''
    try:
        root = etree.fromstring(rib_xml.encode())
        # Define namespaces for OpenConfig YANG
        ns = {
            'oc-ni': 'http://openconfig.net/yang/network-instance',
            'oc-if': 'http://openconfig.net/yang/interfaces',
            'oc-ip': 'http://openconfig.net/yang/interfaces/ip',
            'oc-pol': 'http://openconfig.net/yang/policy-types',
            'oc-bgp': 'http://openconfig.net/yang/bgp',
            'oc-ospf': 'http://openconfig.net/yang/ospf'
        }
        # First, extract interface information to get loopback IP and all interface IPs
        interfaces = {}
        for iface in root.xpath('//oc-if:interface', namespaces=ns):
            name = iface.xpath('oc-if:name/text()', namespaces=ns)
            if not name:
                continue
            name = name[0]
            interfaces[name] = {'ipv4': [], 'ipv6': []}
            # Get IPv4 addresses
            for ipv4 in iface.xpath('.//oc-ip:ipv4/oc-ip:addresses/oc-ip:address', namespaces=ns):
                ip = ipv4.xpath('oc-ip:ip/text()', namespaces=ns)
                prefix = ipv4.xpath('oc-ip:config/oc-ip:prefix-length/text()', namespaces=ns)
                if ip and prefix:
                    interfaces[name]['ipv4'].append(f"{ip[0]}/{prefix[0]}")
            # Get IPv6 addresses
            for ipv6 in iface.xpath('.//oc-ip:ipv6/oc-ip:addresses/oc-ip:address', namespaces=ns):
                ip = ipv6.xpath('oc-ip:ip/text()', namespaces=ns)
                prefix = ipv6.xpath('oc-ip:config/oc-ip:prefix-length/text()', namespaces=ns)
                if ip and prefix:
                    interfaces[name]['ipv6'].append(f"{ip[0]}/{prefix[0]}")
        # Find loopback IP (assuming interface named Loopback0)
        if 'Loopback0' in interfaces and interfaces['Loopback0']['ipv4']:
            loopback_ip = interfaces['Loopback0']['ipv4'][0].split('/')[0]
        # Get router hostname from network instance config
        hostname = root.xpath('//oc-ni:config/oc-ni:name/text()', namespaces=ns)
        router_name = hostname[0] if hostname else router_name
        # 1. Connected Routes (interface IPs) - Auto-learned from interface data
        for iface, ips in interfaces.items():
            for ip in ips['ipv4']:
                network = ip.split('/')[0]
                prefix = ip.split('/')[1]
                # Skip /32 addresses as they are typically loopback/local
                if prefix == '32':
                    continue
                route_entry = {
                    'Router': router_name,
                    'Loopback IP': loopback_ip,
                    'Protocol': 'Connected',
                    'Destination': f"{network}/{prefix}",
                    'Interface': iface,
                    'Next Hop': 'Direct'
                }
                routes.append(route_entry)
                rib_db_manage.add_entry(router_name, loopback_ip, 'Connected', f"{network}/{prefix}", 
                                      iface, 'Direct')
        # 2. Local Routes (loopback interfaces) - Auto-learned
        for iface, ips in interfaces.items():
            for ip in ips['ipv4']:
                network = ip.split('/')[0]
                prefix = ip.split('/')[1]
                # /32 addresses are typically local/loopback routes
                if prefix == '32' or 'Loopback' in iface:
                    route_entry = {
                        'Router': router_name,
                        'Loopback IP': loopback_ip,
                        'Protocol': 'Local',
                        'Destination': f"{network}/{prefix}",
                        'Interface': iface,
                        'Next Hop': 'Direct'
                    }
                    routes.append(route_entry)
                    rib_db_manage.add_entry(router_name, loopback_ip, 'Local', f"{network}/{prefix}", 
                                          iface, 'Direct')
        # 3. Static Routes - From network instance static configuration
        for route in root.xpath('//oc-ni:protocol[oc-ni:identifier="oc-pol:STATIC"]/oc-ni:static-routes/oc-ni:static', namespaces=ns):
            prefix = route.xpath('oc-ni:prefix/text()', namespaces=ns)
            if not prefix:
                continue
            prefix = prefix[0]
            next_hops = route.xpath('.//oc-ni:next-hop', namespaces=ns)
            for nh in next_hops:
                next_hop = nh.xpath('oc-ni:config/oc-ni:next-hop/text()', namespaces=ns)
                interface = nh.xpath('oc-ni:interface-ref/oc-ni:config/oc-ni:interface/text()', namespaces=ns)
                route_entry = {
                    'Router': router_name,
                    'Loopback IP': loopback_ip,
                    'Protocol': 'Static',
                    'Destination': prefix,
                    'Interface': interface[0] if interface else 'N/A',
                    'Next Hop': next_hop[0] if next_hop else 'Direct'
                }
                routes.append(route_entry)
                rib_db_manage.add_entry(router_name, loopback_ip, 'Static', prefix, 
                                      interface[0] if interface else 'N/A', 
                                      next_hop[0] if next_hop else 'Direct')
        # 4. OSPF Routes - From OSPF protocol configuration
        for route in root.xpath('//oc-ni:protocol[oc-ni:identifier="oc-pol:OSPF"]/oc-ni:ospf/oc-ni:routes/oc-ni:route', namespaces=ns):
            prefix = route.xpath('oc-ni:prefix/text()', namespaces=ns)
            next_hop = route.xpath('oc-ni:next-hop/text()', namespaces=ns)
            outgoing_if = route.xpath('oc-ni:outgoing-interface/text()', namespaces=ns)
            if prefix and next_hop:
                route_entry = {
                    'Router': router_name,
                    'Loopback IP': loopback_ip,
                    'Protocol': 'OSPF',
                    'Destination': prefix[0],
                    'Interface': outgoing_if[0] if outgoing_if else 'N/A',
                    'Next Hop': next_hop[0]
                }
                routes.append(route_entry)
                rib_db_manage.add_entry(router_name, loopback_ip, 'OSPF', prefix[0], 
                                      outgoing_if[0] if outgoing_if else 'N/A', next_hop[0])
        # 5. BGP Routes - From BGP protocol configuration
        for route in root.xpath('//oc-ni:protocol[oc-ni:identifier="oc-pol:BGP"]/oc-ni:bgp/oc-ni:rib/oc-ni:afi-safis/oc-ni:afi-safi/oc-ni:ipv4-unicast/oc-ni:routes/oc-ni:route', namespaces=ns):
            prefix = route.xpath('oc-ni:prefix/text()', namespaces=ns)
            next_hop = route.xpath('oc-ni:state/oc-ni:next-hop/text()', namespaces=ns)
            if prefix and next_hop:
                # Try to find the outgoing interface for this next hop
                outgoing_if = None
                for iface, ips in interfaces.items():
                    for ip in ips['ipv4'] + ips['ipv6']:
                        if ip.startswith(next_hop[0]):
                            outgoing_if = iface
                            break
                    if outgoing_if:
                        break
                route_entry = {
                    'Router': router_name,
                    'Loopback IP': loopback_ip,
                    'Protocol': 'BGP',
                    'Destination': prefix[0],
                    'Interface': outgoing_if if outgoing_if else 'N/A',
                    'Next Hop': next_hop[0]
                }
                routes.append(route_entry)
                rib_db_manage.add_entry(router_name, loopback_ip, 'BGP', prefix[0], 
                                      outgoing_if if outgoing_if else 'N/A', next_hop[0])
        # 6. Additional route types that might be present
        # Direct routes (from interface configuration)
        for iface, ips in interfaces.items():
            for ip in ips['ipv4']:
                network = ip.split('/')[0]
                prefix = ip.split('/')[1]
                # Check if this is a direct route (not already covered)
                if prefix != '32' and 'Loopback' not in iface:
                    # Check if this route is not already added as Connected
                    existing_route = next((r for r in routes if r['Destination'] == f"{network}/{prefix}" and r['Protocol'] == 'Connected'), None)
                    if not existing_route:
                        route_entry = {
                            'Router': router_name,
                            'Loopback IP': loopback_ip,
                            'Protocol': 'Direct',
                            'Destination': f"{network}/{prefix}",
                            'Interface': iface,
                            'Next Hop': 'Direct'
                        }
                        routes.append(route_entry)
                        rib_db_manage.add_entry(router_name, loopback_ip, 'Direct', f"{network}/{prefix}", 
                                              iface, 'Direct')
        print(f"✅ Parsed {len(routes)} routes from {router_name}")
        print(f"   - Connected: {len([r for r in routes if r['Protocol'] == 'Connected'])}")
        print(f"   - Local: {len([r for r in routes if r['Protocol'] == 'Local'])}")
        print(f"   - Static: {len([r for r in routes if r['Protocol'] == 'Static'])}")
        print(f"   - OSPF: {len([r for r in routes if r['Protocol'] == 'OSPF'])}")
        print(f"   - BGP: {len([r for r in routes if r['Protocol'] == 'BGP'])}")
        print(f"   - Direct: {len([r for r in routes if r['Protocol'] == 'Direct'])}")
        return routes
    except Exception as e:
        print(f"Error parsing Arista RIB XML: {e}")
        import traceback
        traceback.print_exc()
        return []
