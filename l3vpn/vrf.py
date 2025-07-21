from lxml import etree
from ncclient import manager
from ncclient.transport.errors import AuthenticationError, SSHError
from ncclient.operations import RPCError
import logging

class VRFManager:
    PLATFORM_MODELS = {
        'iosxe': {
            'native': "http://cisco.com/ns/yang/Cisco-IOS-XE-native",
            'vrf': "http://cisco.com/ns/yang/Cisco-IOS-XE-vrf"
        },
        'iosxr': {
            'vrf': "http://cisco.com/ns/yang/Cisco-IOS-XR-vrf-cfg"
        }
    }

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.platform = None
        self.namespaces = None
        self.conn = None

    def connect(self):
        try:
            self.conn = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=False,
                device_params={'name': 'csr' if 'iosxe' in str(self.conn.server_capabilities) else 'iosxr'},
                timeout=30
            )
            caps = str(self.conn.server_capabilities)
            if 'Cisco-IOS-XE' in caps:
                self.platform = 'iosxe'
                self.namespaces = self.PLATFORM_MODELS['iosxe']
            elif 'Cisco-IOS-XR' in caps:
                self.platform = 'iosxr'
                self.namespaces = self.PLATFORM_MODELS['iosxr']
            else:
                raise Exception("Unsupported platform")
            return True
        except (AuthenticationError, SSHError) as e:
            raise Exception(f"Connection failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Platform detection failed: {str(e)}")

    def close(self):
        if self.conn:
            self.conn.close_session()

class WebVRFManager(VRFManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('vrf_web')

    def connect(self):
        try:
            self.conn = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=False,
                device_params={'name': 'csr'},  # Always use csr for IOS XE
                timeout=30
            )
            caps = str(self.conn.server_capabilities)
            if 'Cisco-IOS-XE' in caps:
                self.platform = 'iosxe'
                self.namespaces = self.PLATFORM_MODELS['iosxe']
            elif 'Cisco-IOS-XR' in caps:
                self.platform = 'iosxr'
                self.namespaces = self.PLATFORM_MODELS['iosxr']
            else:
                raise Exception("Unsupported platform")
            return True
        except (AuthenticationError, SSHError) as e:
            raise Exception(f"Connection failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Platform detection failed: {str(e)}")

    def create_vrf(self, vrf_name, rd, route_targets, description=""):
        try:
            self._validate_input_encoding(vrf_name, rd, route_targets, description)
            if self.platform == 'iosxe':
                import_rt = next((rt.split(',')[1] for rt in route_targets if rt.startswith('import,')), '')
                export_rt = next((rt.split(',')[1] for rt in route_targets if rt.startswith('export,')), '')
                config = f"""
                <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                    <vrf>
                      <definition>
                        <name>{vrf_name}</name>
                        <rd>{rd}</rd>
                        {f'<description>{description}</description>' if description else ''}
                        <address-family>
                          <ipv4/>
                        </address-family>
                        <route-target>
                          <export>
                            <asn-ip>{export_rt}</asn-ip>
                          </export>
                          <import>
                            <asn-ip>{import_rt}</asn-ip>
                          </import>
                        </route-target>
                      </definition>
                    </vrf>
                  </native>
                </config>
                """
                print("\n--- XML SENT TO DEVICE ---\n")
                print(config)
                print("\n-------------------------\n")
                response = self.conn.edit_config(target='running', config=config)
            elif self.platform == 'iosxr':
                config = self._build_web_iosxr_config(vrf_name, rd, route_targets, description)
                response = self._safe_edit_config(config)
            else:
                raise Exception(f"VRF creation not implemented for {self.platform}")
            return self._format_web_response(response)
        except Exception as e:
            self.logger.error(f"Web VRF creation failed: {str(e)}")
            raise

    def _validate_input_encoding(self, *args):
        for arg in args:
            if isinstance(arg, str) and any(c in arg for c in ['&', '<', '>', '"', "'"]):
                raise ValueError("Invalid XML characters in input")

    def _build_working_iosxe_config(self, vrf_name, rd, route_targets, description):
        import_rt = next((rt.split(',')[1] for rt in route_targets if rt.startswith('import,')), '')
        export_rt = next((rt.split(',')[1] for rt in route_targets if rt.startswith('export,')), '')
        return f'''
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
            <vrf>
              <definition>
                <name>{vrf_name}</name>
                <rd>{rd}</rd>
                <address-family>
                  <ipv4/>
                </address-family>
                <route-target>
                  <export>
                    <asn-ip>{export_rt}</asn-ip>
                  </export>
                  <import>
                    <asn-ip>{import_rt}</asn-ip>
                  </import>
                </route-target>
              </definition>
            </vrf>
          </native>
        </config>
        '''

    def _create_iosxe_rpc(self, config):
        # For IOS XE, the config is already wrapped, so just use as is
        return config

    def _safe_dispatch(self, rpc):
        try:
            return self.conn.dispatch(etree.fromstring(rpc.encode('utf-8')))
        except etree.XMLSyntaxError as e:
            self.logger.error(f"XML syntax error: {str(e)}")
            raise

    def _build_web_iosxr_config(self, vrf_name, rd, route_targets, description):
        ns = self.namespaces['vrf']
        root = etree.Element(f"{{{ns}}}vrf")
        vrf_list = etree.SubElement(root, "vrf-list")
        etree.SubElement(vrf_list, "vrf-name").text = vrf_name
        etree.SubElement(vrf_list, "create")
        rd_elem = etree.SubElement(vrf_list, "rd")
        etree.SubElement(rd_elem, "rd").text = rd
        if description:
            etree.SubElement(vrf_list, "vrf-description").text = description
        af = etree.SubElement(vrf_list, "address-family")
        ipv4 = etree.SubElement(af, "ipv4")
        unicast = etree.SubElement(ipv4, "unicast")
        import_elem = etree.SubElement(unicast, "import")
        rt_elem = etree.SubElement(import_elem, "route-target")
        for direction, target in [rt.split(',') for rt in route_targets]:
            if direction == 'import':
                elem = etree.SubElement(rt_elem, "import")
            else:
                elem = etree.SubElement(rt_elem, "export")
            etree.SubElement(elem, "asn-ip").text = target
        return etree.tostring(root, encoding='unicode')

    def _safe_edit_config(self, config):
        try:
            parsed = etree.fromstring(config.encode('utf-8'))
            return self.conn.edit_config(target='running', config=parsed)
        except etree.XMLSyntaxError as e:
            self.logger.error(f"Invalid XML config: {str(e)}")
            raise

    def _format_web_response(self, response):
        return {
            'success': True,
            'xml_received': str(response.xml),
            'device_response': str(response)
        } 