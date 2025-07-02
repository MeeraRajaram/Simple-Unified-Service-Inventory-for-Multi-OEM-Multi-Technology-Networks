from ncclient import manager
from lxml import etree
from tabulate import tabulate
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('service_discovery.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class ServiceDiscovery:
    def __init__(self, host, username, password, port=830, timeout=30):
        self.device_params = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "hostkey_verify": False,
            "device_params": {'name': 'default'},
            "timeout": timeout
        }
        
        # Protocol capabilities and their XML filters
        self.protocols = {
            'vlan': {
                'filter': 'vlans',
                'xpath': 'vlans/vlan',
                'columns': ['name', 'vlan-id', 'description'],
                'namespace': None
            },
            'mpls': {
                'filter': 'mpls',
                'xpath': 'mpls',
                'columns': ['admin-status', 'statistics-timer'],
                'namespace': None
            },
            'mvpn': {
                'filter': 'protocols/mvpn',
                'xpath': 'protocols/mvpn',
                'columns': ['disabled', 'traceoptions'],
                'namespace': None
            },
            'l3vpn': {
                'filter': 'routing-instances/instance[instance-type="vrf"]',
                'xpath': 'routing-instances/instance[instance-type="vrf"]',
                'columns': ['name', 'interface', 'route-distinguisher'],
                'namespace': None
            },
            'l2vpn': {
                'filter': 'protocols/l2vpn',
                'xpath': 'protocols/l2vpn',
                'columns': ['traceoptions', 'site'],
                'namespace': None
            },
            'vrf': {
                'filter': 'routing-instances',
                'xpath': 'routing-instances/instance',
                'columns': ['name', 'instance-type', 'interface'],
                'namespace': None
            }
        }

    def connect(self):
        """Establish NETCONF connection"""
        try:
            self.conn = manager.connect(**self.device_params)
            logging.info(f"Connected to {self.device_params['host']}")
            return True
        except Exception as e:
            logging.error(f"Connection failed: {str(e)}")
            return False

    def _build_filter(self, protocol):
        """Dynamically build XML filter for protocol"""
        filter_str = f'''
        <filter>
            <configuration>
                <{protocol['filter']}/>
            </configuration>
        </filter>
        '''
        return filter_str

    def _parse_response(self, response, protocol):
        """Parse XML response and extract data"""
        try:
            root = etree.fromstring(response.xml)
            elements = root.findall(f'.//{protocol["xpath"]}', namespaces=protocol['namespace'])
            
            if not elements:
                logging.debug(f"No configuration found for {protocol['filter']}")
                return None

            results = []
            for elem in elements:
                item = {}
                for col in protocol['columns']:
                    child = elem.find(col)
                    item[col] = child.text if child is not None else "N/A"
                results.append(item)
            
            return results
        except Exception as e:
            logging.error(f"Parsing error for {protocol['filter']}: {str(e)}")
            return None

    def check_protocol(self, protocol_name):
        """Check specific protocol configuration"""
        if protocol_name not in self.protocols:
            logging.error(f"Unknown protocol: {protocol_name}")
            return None

        protocol = self.protocols[protocol_name]
        try:
            filter_xml = self._build_filter(protocol)
            response = self.conn.get(filter=filter_xml)
            logging.debug(f"Raw response for {protocol_name}:\n{response.xml}")
            
            return self._parse_response(response, protocol)
        except Exception as e:
            logging.error(f"Protocol check failed for {protocol_name}: {str(e)}")
            return None

    def discover_all(self):
        """Discover all configured protocols"""
        if not hasattr(self, 'conn') or not self.conn.connected:
            logging.error("Not connected to device")
            return None

        results = {}
        for protocol_name in self.protocols:
            logging.info(f"Checking {protocol_name} configuration...")
            config = self.check_protocol(protocol_name)
            results[protocol_name] = config if config else "Not configured"
        
        return results

    def print_results(self, results):
        """Print results in tabulated format"""
        print("\n=== Service Configuration Summary ===")
        for protocol, data in results.items():
            print(f"\n{protocol.upper()} Configuration:")
            if isinstance(data, list):
                print(tabulate(data, headers='keys', tablefmt='grid'))
            else:
                print(data)

    def get_device_info(self):
        """Get basic device information"""
        try:
            system_info = self.conn.get_system_information()
            root = etree.fromstring(str(system_info))
            
            return {
                'hostname': root.findtext('.//host-name') or 'N/A',
                'model': root.findtext('.//hardware-model') or 'N/A',
                'serial': root.findtext('.//serial-number') or 'N/A',
                'os_version': root.findtext('.//version') or 'N/A'
            }
        except Exception as e:
            logging.error(f"Failed to get device info: {str(e)}")
            return {
                'hostname': 'N/A',
                'model': 'N/A',
                'serial': 'N/A',
                'os_version': 'N/A'
            }

    def close(self):
        """Close connection"""
        if hasattr(self, 'conn'):
            self.conn.close_session()
            logging.info("Connection closed")

def main():
    # Example usage
    discovery = ServiceDiscovery(
        host="10.0.13.2",
        username="admin",
        password="sshadmin123"
    )

    if not discovery.connect():
        sys.exit(1)

    try:
        # Get device info
        device_info = discovery.get_device_info()
        print("\n=== Device Information ===")
        for key, value in device_info.items():
            print(f"{key.title()}: {value}")

        # Discover all services
        results = discovery.discover_all()
        discovery.print_results(results)

    finally:
        discovery.close()

if __name__ == "__main__":
    main()