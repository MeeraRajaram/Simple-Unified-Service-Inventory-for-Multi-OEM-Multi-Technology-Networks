from flask import Blueprint, render_template, redirect, url_for, request
from services.db import router_db
from ncclient import manager
import traceback
import subprocess
import time

# Import vendor-specific inventory functions
from services_physical.cisco_phy import get_physical_inventory as cisco_phy
from services_physical.juniper_phy import get_physical_inventory as juniper_phy
from services_physical.arista_phy import get_physical_inventory as arista_phy
from services_physical.cisco_serv import discover_services as cisco_serv
from services_physical.juniper_serv import discover_services as juniper_serv
from services_physical.arista_serv import ServiceDiscovery as AristaServiceDiscovery

services_physical_bp = Blueprint('services_physical', __name__, url_prefix='/services-physical')

services_physical_cache = None

@services_physical_bp.route('/', methods=['GET'])
def services_physical_home():
    global services_physical_cache
    if services_physical_cache is not None:
        return render_template('services_physical/services_physical.html', routers=services_physical_cache)
    routers = router_db.get_routers()
    results = []
    for router in routers:
        hostname, software_version, ip, vendor, username, password = router
        router_result = {
            'hostname': hostname,
            'ip': ip,
            'vendor': vendor,
            'physical': None,
            'services': None,
            'phy_error': None,
            'serv_error': None
        }
        try:
            with manager.connect(
                host=ip,
                port=830,
                username=username,
                password=password,
                hostkey_verify=False,
                allow_agent=False,
                look_for_keys=False,
                timeout=60
            ) as m:
                # PHYSICAL INVENTORY
                try:
                    if vendor.lower() == 'cisco':
                        phy = cisco_phy(m)
                        router_result['physical'] = str(phy) if phy else 'No data.'
                    elif vendor.lower() == 'juniper':
                        # Physical Inventory: call the test script as a subprocess
                        try:
                            result_phy = subprocess.run(
                                [
                                    'python3', 'services_physical/juniper_phy_test.py',
                                    '--host', ip,
                                    '--username', username,
                                    '--password', password
                                ],
                                capture_output=True, text=True, check=True
                            )
                            output_phy = result_phy.stdout
                        except Exception as e:
                            output_phy = f"Error running juniper_phy_test.py: {e}"
                        print(f"[DEBUG] Output from juniper_phy_test.py for {ip}:\n{output_phy}")
                        router_result['physical'] = output_phy if output_phy else 'No data.'
                    elif vendor.lower() == 'arista':
                        print(f"[DEBUG] Attempting Arista NETCONF connection: IP={ip}, username={username}, password={password}")
                        start_time = time.time()
                        try:
                            with manager.connect(
                                host=ip,
                                port=830,
                                username=username,
                                password=password,
                                hostkey_verify=False,
                                allow_agent=False,
                                look_for_keys=False,
                                timeout=60  # Increased timeout
                            ) as m:
                                phy = arista_phy(m)
                                router_result['physical'] = str(phy) if phy else 'No data.'
                        except Exception as e:
                            elapsed = time.time() - start_time
                            print(f"[DEBUG] Arista NETCONF connection failed after {elapsed:.2f} seconds: {e}")
                            router_result['phy_error'] = f"NETCONF connection failed: {e}"
                    else:
                        router_result['phy_error'] = f"Unknown vendor: {vendor}"
                except Exception as e:
                    router_result['phy_error'] = f"Error: {e}\n{traceback.format_exc()}"
                # SERVICES INVENTORY
                try:
                    if vendor.lower() == 'cisco':
                        import io
                        import sys
                        buf = io.StringIO()
                        sys_stdout = sys.stdout
                        sys.stdout = buf
                        cisco_serv(m)
                        sys.stdout = sys_stdout
                        router_result['services'] = buf.getvalue()
                    elif vendor.lower() == 'juniper':
                        # Physical Inventory: call the test script as a subprocess
                        try:
                            result_phy = subprocess.run(
                                [
                                    'python3', 'services_physical/juniper_phy_test.py',
                                    '--host', ip,
                                    '--username', username,
                                    '--password', password
                                ],
                                capture_output=True, text=True, check=True
                            )
                            output_phy = result_phy.stdout
                        except Exception as e:
                            output_phy = f"Error running juniper_phy_test.py: {e}"
                        print(f"[DEBUG] Output from juniper_phy_test.py for {ip}:\n{output_phy}")
                        router_result['physical'] = output_phy if output_phy else 'No data.'
                        # Services Inventory: call the test script as a subprocess
                        try:
                            result_serv = subprocess.run(
                                [
                                    'python3', 'services_physical/juniper_serv_test.py',
                                    '--host', ip,
                                    '--username', username,
                                    '--password', password
                                ],
                                capture_output=True, text=True, check=True
                            )
                            output_serv = result_serv.stdout
                        except Exception as e:
                            output_serv = f"Error running juniper_serv_test.py: {e}"
                        print(f"[DEBUG] Output from juniper_serv_test.py for {ip}:\n{output_serv}")
                        router_result['services'] = output_serv if output_serv else 'No data.'
                    elif vendor.lower() == 'arista':
                        arista = AristaServiceDiscovery(ip, username, password, timeout=60)
                        if arista.connect():
                            results_dict = arista.discover_all()
                            import io
                            import sys
                            buf = io.StringIO()
                            sys_stdout = sys.stdout
                            sys.stdout = buf
                            arista.print_results(results_dict)
                            sys.stdout = sys_stdout
                            router_result['services'] = buf.getvalue()
                            arista.close()
                        else:
                            router_result['serv_error'] = 'Could not connect.'
                    else:
                        router_result['serv_error'] = f"Unknown vendor: {vendor}"
                except Exception as e:
                    router_result['serv_error'] = f"Error: {e}\n{traceback.format_exc()}"
        except Exception as e:
            router_result['phy_error'] = f"NETCONF connection failed: {e}"
            router_result['serv_error'] = f"NETCONF connection failed: {e}"
        results.append(router_result)
    services_physical_cache = results
    return render_template('services_physical/services_physical.html', routers=results)

@services_physical_bp.route('/refresh', methods=['POST'])
def services_physical_refresh():
    global services_physical_cache
    services_physical_cache = None
    return redirect(url_for('services_physical.services_physical_home')) 