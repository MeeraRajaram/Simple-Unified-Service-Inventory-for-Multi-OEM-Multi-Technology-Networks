from ncclient import manager
from lxml import etree
from rib import juniper_parse
from rib.db_utils import rib_db_manage

def get_routing_info(m):
    # 1. Try IETF Routing YANG
    try:
        print("🔍 Trying IETF Routing YANG...")
        ietf_filter = '''
        <routing xmlns=\"urn:ietf:params:xml:ns:yang:ietf-routing\"/>
        '''
        response = m.get_config(source="running", filter=("subtree", ietf_filter))
        if b'<routing' in response.xml.encode():
            print("✅ IETF Routing info found.")
            return response.data_xml
    except Exception as e:
        print(f"❌ IETF Routing failed: {e}")
    # 2. Try OpenConfig Routing Protocols
    try:
        print("🔍 Trying OpenConfig routing...")
        oc_filter = '''
        <network-instances xmlns=\"http://openconfig.net/yang/network-instance\">
          <network-instance>
            <protocols>
              <protocol/>
            </protocols>
          </network-instance>
        </network-instances>
        '''
        response = m.get_config(source="running", filter=("subtree", oc_filter))
        if b'<network-instances' in response.xml.encode():
            print("✅ OpenConfig Routing info found.")
            return response.data_xml
    except Exception as e:
        print(f"❌ OpenConfig Routing failed: {e}")
    # 3. Try Junos Native RPC (Fallback)
    try:
        print("🔍 Trying Junos native routing RPC...")
        rpc = etree.XML('''
        <get-route-information>
            <table>inet.0</table>
        </get-route-information>
        ''')
        response = m.dispatch(rpc)
        xml_str = str(response)
        print(xml_str)
        return xml_str
    except Exception as e:
        print(f"❌ Junos native RPC failed: {e}")
    return None

def handle_routing_info(hostname, ip, username, password):
    print(f"[Juniper] Handling routing info for {hostname} ({ip}) with user {username}")
    router = {
        'host': ip,
        'port': 830,
        'username': username,
        'password': password,
        'hostkey_verify': False,
        'device_params': {'name': 'junos'},
        'allow_agent': False,
        'look_for_keys': False,
        'timeout': 10
    }
    try:
        with manager.connect(**router) as m:
            xml_str = get_routing_info(m)
            if not xml_str:
                raise Exception("No routing XML could be retrieved.")
            print(f"✅ Routing XML for {hostname} collected")
            routes = juniper_parse.parse_juniper_rpc_xml(xml_str, hostname)
            return {
                'success': True,
                'hostname': hostname,
                'rib_xml': xml_str,
                'routes': routes
            }
    except Exception as e:
        error_msg = f"Failed to get RIB from {hostname} ({ip}): {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'hostname': hostname,
            'error': error_msg
        }

def parse_juniper_rpc_xml(xml_data, hostname='Juniper-Router'):
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
        # Next hop and interface
        nh = entry.find('nh')
        if nh is not None:
            next_hop = nh.findtext('to') or nh.findtext('nh-local-interface') or 'N/A'
            interface = nh.findtext('via') or nh.findtext('nh-local-interface') or 'N/A'
        else:
            next_hop = 'N/A'
            interface = 'N/A'
        # Special case for protocol
        if protocol.lower() == 'local':
            next_hop = 'Local'
        elif protocol.lower() == 'direct':
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
