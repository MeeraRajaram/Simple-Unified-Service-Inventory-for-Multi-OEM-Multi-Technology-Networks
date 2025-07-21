from flask import Flask
from blueprints.main import main_bp
from blueprints.inventory import inventory_bp
from blueprints.scan import scan_bp
from blueprints.rib import rib_bp
from blueprints.services_physical import services_physical_bp
from blueprints.topology.topology import topology_bp
from blueprints.view import view_bp
from blueprints.pathfinder import pathfinder_bp
from blueprints.configuration_push import configuration_push_bp
import socket
from flask import request, jsonify
from ncclient import manager
from lxml import etree
import re

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Configure JSON handling
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(scan_bp)
app.register_blueprint(rib_bp)
app.register_blueprint(services_physical_bp)
app.register_blueprint(topology_bp)
app.register_blueprint(pathfinder_bp)
app.register_blueprint(configuration_push_bp)

def find_free_port(start_port=5001, max_port=5100):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found in range.")

@app.route('/api/create-vrf', methods=['POST'])
def create_vrf():
    data = request.get_json()
    routers = data['routers']
    username = data['username']
    password = data['password']
    vrf = data['vrf']
    results = []

    for router in routers:
        loopback_ip = router['loopback_ip']
        device = {
            "host": loopback_ip,
            "port": 830,
            "username": username,
            "password": password,
            "hostkey_verify": False
        }
        try:
            with manager.connect(**device) as m:
                # 1. Create VRF if not present
                vrf_config = f"""
                <config>
                  <native xmlns=\"http://cisco.com/ns/yang/Cisco-IOS-XE-native\">
                    <vrf>
                      <definition>
                        <name>{vrf['name']}</name>
                        {f'<description>{vrf.get('description','')}</description>' if vrf.get('description') else ''}
                        <rd>{vrf['rd']}</rd>
                        <address-family>
                          <ipv4 />
                        </address-family>
                      </definition>
                    </vrf>
                  </native>
                </config>
                """
                m.edit_config(target='running', config=vrf_config)
                # 2. For each interface
                for intf in router['interfaces']:
                    intf_name = intf['name']
                    # Remove old VRF assignment
                    intf_type_match = re.match(r'^([a-zA-Z]+)([0-9/]+)$', intf_name)
                    if not intf_type_match:
                        continue
                    intf_type, intf_num = intf_type_match.groups()
                    yang_intf_type = intf_type if intf_type[0].isupper() else intf_type.capitalize()
                    remove_vrf_config = f"""
                    <config>
                      <native xmlns=\"http://cisco.com/ns/yang/Cisco-IOS-XE-native\">
                        <interface>
                          <{yang_intf_type}>
                            <name>{intf_num}</name>
                            <vrf operation=\"delete\">
                              <forwarding/>
                            </vrf>
                          </{yang_intf_type}>
                        </interface>
                      </native>
                    </config>
                    """
                    m.edit_config(target='running', config=remove_vrf_config)
                    # Assign new VRF
                    assign_vrf_config = f"""
                    <config>
                      <native xmlns=\"http://cisco.com/ns/yang/Cisco-IOS-XE-native\">
                        <interface>
                          <{yang_intf_type}>
                            <name>{intf_num}</name>
                            <vrf>
                              <forwarding>{vrf['name']}</forwarding>
                            </vrf>
                          </{yang_intf_type}>
                        </interface>
                      </native>
                    </config>
                    """
                    m.edit_config(target='running', config=assign_vrf_config)
                    # Optionally reapply IP
                    if 'ip' in intf and 'mask' in intf:
                        ip_config = f"""
                        <config>
                          <native xmlns=\"http://cisco.com/ns/yang/Cisco-IOS-XE-native\">
                            <interface>
                              <{yang_intf_type}>
                                <name>{intf_num}</name>
                                <ip>
                                  <address>
                                    <primary>
                                      <address>{intf['ip']}</address>
                                      <mask>{intf['mask']}</mask>
                                    </primary>
                                  </address>
                                </ip>
                              </{yang_intf_type}>
                            </interface>
                          </native>
                        </config>
                        """
                        m.edit_config(target='running', config=ip_config)
                results.append({"router": router['name'], "success": True, "message": "Configured"})
        except Exception as e:
            results.append({"router": router['name'], "success": False, "message": str(e)})

    return jsonify({"results": results, "success": all(r['success'] for r in results)})

if __name__ == '__main__':
    port = 5006
    print(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port) 