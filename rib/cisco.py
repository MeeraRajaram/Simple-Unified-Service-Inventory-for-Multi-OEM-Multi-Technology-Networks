from ncclient import manager
from lxml import etree
from rib import cisco_parse

def handle_routing_info(hostname, ip, username, password):
    print(f"[Cisco] Handling routing info for {hostname} ({ip}) with user {username}")
    router = {
        'host': ip,
        'port': 830,
        'username': username,
        'password': password,
        'hostkey_verify': False,
        'device_params': {'name': 'csr'}
    }
    routing_filter = """
    <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <routing-state xmlns="urn:ietf:params:xml:ns:yang:ietf-routing"/>
    </filter>
    """
    try:
        with manager.connect(**router) as m:
            print(f"Connected to {hostname}. Getting routing table (RIB)...")
            response = m.get(routing_filter)
            root = etree.Element("router", name=hostname, ip=ip)
            root.append(response.data.getchildren()[0])
            rib_xml = etree.tostring(
                root,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8'
            ).decode()
            print(f"✅ NETCONF RIB for {hostname} collected")
            routes = cisco_parse.parse_rib_xml(rib_xml, hostname, ip)
            return {
                'success': True,
                'hostname': hostname,
                'rib_xml': rib_xml,
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
