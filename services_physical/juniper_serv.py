from ncclient import manager
from lxml import etree
from tabulate import tabulate

# Capabilities to check (with NETCONF filters)
CAPABILITIES = {
    'vlan': {
        'filter': '''
            <filter>
                <configuration>
                    <vlans/>
                </configuration>
            </filter>
        ''',
        'xpath': '//vlans/vlan',
        'columns': ['name', 'vlan-id', 'description']
    },
    'mvpn': {
        'filter': '''
            <filter>
                <configuration>
                    <protocols>
                        <mvpn/>
                    </protocols>
                </configuration>
            </filter>
        ''',
        'xpath': '//mvpn',
        'columns': ['disabled', 'traceoptions']
    },
    'l3vpn': {
        'filter': '''
            <filter>
                <configuration>
                    <routing-instances>
                        <instance>
                            <instance-type>vrf</instance-type>
                        </instance>
                    </routing-instances>
                </configuration>
            </filter>
        ''',
        'xpath': '//instance[instance-type="vrf"]',
        'columns': ['name', 'interface', 'route-distinguisher']
    },
    'l2vpn': {
        'filter': '''
            <filter>
                <configuration>
                    <protocols>
                        <l2vpn/>
                    </protocols>
                </configuration>
            </filter>
        ''',
        'xpath': '//l2vpn',
        'columns': ['traceoptions', 'site']
    },
    'vrf': {
        'filter': '''
            <filter>
                <configuration>
                    <routing-instances/>
                </configuration>
            </filter>
        ''',
        'xpath': '//instance',
        'columns': ['name', 'instance-type', 'interface']
    }
}

def check_capability(conn, capability):
    """Fetch and parse capability data using NETCONF"""
    try:
        # Get configuration data
        config = conn.get_config(source='running', filter=capability['filter'])
        root = etree.fromstring(str(config))
        
        # Extract data using XPath
        elements = root.xpath(capability['xpath'])
        
        if not elements:
            return None
        
        # Parse results
        results = []
        for elem in elements:
            item = {}
            for col in capability['columns']:
                child = elem.find(col)
                item[col] = child.text if child is not None else "N/A"
            results.append(item)
        
        return results
    except Exception as e:
        print(f"Error checking capability: {str(e)}")
        return None

def discover_services(conn):
    """Check all capabilities and print results"""
    if not conn:
        print("No active connection")
        return
    
    try:
        # Check each capability
        for cap_name, cap_params in CAPABILITIES.items():
            results = check_capability(conn, cap_params)
            
            print(f"\n{cap_name.upper()} Configuration:")
            if results:
                print(tabulate(results, headers='keys', tablefmt='grid'))
            else:
                print("Service not configured")
                
    except Exception as e:
        print(f"Error during service discovery: {str(e)}")

def get_device_info(conn):
    """Get basic device information"""
    try:
        # Get system information
        system_info = conn.get_system_information()
        root = etree.fromstring(str(system_info))
        
        hostname = root.findtext('.//host-name') or 'N/A'
        loopback = get_loopback_ip(conn) or 'N/A'
        
        return {
            'hostname': hostname,
            'loopback': loopback,
            'model': root.findtext('.//hardware-model') or 'N/A',
            'serial': root.findtext('.//serial-number') or 'N/A',
            'os_version': root.findtext('.//junos-version') or 'N/A'
        }
    except Exception as e:
        print(f"Error getting device info: {str(e)}")
        return {
            'hostname': 'N/A',
            'loopback': 'N/A',
            'model': 'N/A',
            'serial': 'N/A',
            'os_version': 'N/A'
        }

def get_loopback_ip(conn):
    """Extract loopback IP address"""
    try:
        filter = '''
            <filter>
                <configuration>
                    <interfaces>
                        <interface>
                            <name>lo0</name>
                        </interface>
                    </interfaces>
                </configuration>
            </filter>
        '''
        config = conn.get_config(source='running', filter=filter)
        root = etree.fromstring(str(config))
        unit = root.find('.//unit')
        if unit is not None:
            return unit.findtext('family/inet/address/name')
        return None
    except Exception:
        return None