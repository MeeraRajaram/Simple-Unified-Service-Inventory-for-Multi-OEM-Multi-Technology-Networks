from ncclient import manager
from lxml import etree
from rib import arista_parse

def handle_routing_info(hostname, ip, username, password):
    print(f"[Arista] Handling routing info for {hostname} ({ip}) with user {username}")
    router = {
        'host': ip,
        'port': 830,
        'username': username,
        'password': password,
        'hostkey_verify': False,
        'device_params': {'name': 'default'}
    }
    
    # Enhanced combined filter to get interfaces and comprehensive routing information
    combined_filter = '''
    <filter xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <interfaces xmlns="http://openconfig.net/yang/interfaces">
        <interface/>
      </interfaces>
      <network-instances xmlns="http://openconfig.net/yang/network-instance">
        <network-instance>
          <name>default</name>
          <protocols>
            <protocol>
              <identifier xmlns:oc-pol="http://openconfig.net/yang/policy-types">oc-pol:STATIC</identifier>
              <name>STATIC</name>
              <static-routes>
                <static/>
              </static-routes>
            </protocol>
            <protocol>
              <identifier xmlns:oc-pol="http://openconfig.net/yang/policy-types">oc-pol:OSPF</identifier>
              <name>OSPF</name>
              <ospf>
                <routes>
                  <route/>
                </routes>
              </ospf>
            </protocol>
            <protocol>
              <identifier xmlns:oc-pol="http://openconfig.net/yang/policy-types">oc-pol:BGP</identifier>
              <name>BGP</name>
              <bgp>
                <rib>
                  <afi-safis>
                    <afi-safi>
                      <ipv4-unicast>
                        <routes>
                          <route/>
                        </routes>
                      </ipv4-unicast>
                    </afi-safi>
                  </afi-safis>
                </rib>
              </bgp>
            </protocol>
          </protocols>
        </network-instance>
      </network-instances>
    </filter>
    '''
    
    try:
        with manager.connect(**router) as m:
            print(f"Connected to {hostname}. Getting comprehensive interfaces and routing table...")
            response = m.get(combined_filter)
            
            # Create a root element with router info
            root = etree.Element("router", name=hostname, ip=ip)
            root.append(response.data.getchildren()[0])
            
            rib_xml = etree.tostring(
                root,
                pretty_print=True,
                xml_declaration=True,
                encoding='UTF-8'
            ).decode()
            
            print(f"✅ Comprehensive NETCONF data for {hostname} collected")
            routes = arista_parse.parse_rib_xml(rib_xml, hostname, ip)
            
            return {
                'success': True,
                'hostname': hostname,
                'rib_xml': rib_xml,
                'routes': routes
            }
            
    except Exception as e:
        error_msg = f"Failed to get data from {hostname} ({ip}): {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'success': False,
            'hostname': hostname,
            'error': error_msg
        }
