from flask import Blueprint, request, jsonify, render_template
import sqlite3
import os
from configuration_push.loopback_fetcher import get_loopback
from l3vpn.vrf_db_manager import init_vrf_db, clear_vrf_db, populate_vrf_db, fetch_all_vrf_rows
from ncclient import manager
from ncclient.transport.errors import AuthenticationError
from l3vpn.vrf import WebVRFManager

configuration_push_bp = Blueprint('configuration_push', __name__)

# In-memory storage for paths (stub)
# Each path: {name, type, routers: {router_name: {ip, exit_interface}}}
paths_data = []

# --- SQLite DB Setup ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'push_data.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS push_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path_name TEXT,
            router_name TEXT,
            router_loopback_ip TEXT,
            router_bgp_support_status TEXT,
            interface_entered_for_push TEXT,
            netconf_username TEXT,
            netconf_password TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@configuration_push_bp.route('/configuration-push')
def configuration_push():
    """Configuration Push page with simple path selection"""
    return render_template('configuration_push.html', paths=paths_data)

@configuration_push_bp.route('/api/paths', methods=['GET'])
def get_paths():
    """Get available paths (always return JSON)"""
    return jsonify({
        'success': True,
        'paths': paths_data if isinstance(paths_data, list) else []
    })

@configuration_push_bp.route('/api/receive-paths', methods=['POST'])
def receive_paths():
    """Receive paths from Path Finder (expects list of dicts with name, type, routers)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No JSON data received'}), 400
        global paths_data
        # Validate and store paths in the expected structure
        paths = data.get('paths', [])
        # Ensure each path has name, type, routers (dict of router_name: {ip, exit_interface})
        valid_paths = []
        for p in paths:
            if 'name' in p and 'type' in p and 'routers' in p:
                valid_paths.append(p)
        paths_data = valid_paths
        # --- Insert initial data into push_data.db ---
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for path in valid_paths:
            path_name = path['name']
            routers = path['routers']
            for router_name, router_info in routers.items():
                loopback_ip = router_info.get('loopback_ip') or router_info.get('ip')
                c.execute('''
                    INSERT INTO push_data (path_name, router_name, router_loopback_ip)
                    VALUES (?, ?, ?)
                ''', (path_name, router_name, loopback_ip))
        conn.commit()
        conn.close()
        return jsonify({
            'success': True,
            'message': f'Received {len(paths_data)} paths',
            'paths': paths_data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@configuration_push_bp.route('/api/create-vrf', methods=['POST'])
def api_create_vrf():
    """Stub for create-vrf endpoint (returns success)"""
    return jsonify({'success': True, 'message': 'VRF creation stub'})

@configuration_push_bp.route('/api/check-bgp-support', methods=['POST'])
def api_check_bgp_support():
    """Stub for BGP support check (returns dummy data)"""
    data = request.get_json() or {}
    router_names = data.get('router_names', [])
    results = {name: True for name in router_names}
    # --- Update BGP support status in push_data.db ---
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for name in router_names:
        c.execute('''
            UPDATE push_data SET router_bgp_support_status=? WHERE router_name=?
        ''', (str(results[name]), name))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'results': results, 'all_supported': all(results.values())}) 

# Add a new endpoint to receive interfaces, netconf username, and password, and update push_data.db
@configuration_push_bp.route('/api/submit-interfaces', methods=['POST'])
def submit_interfaces():
    """Receive interfaces, netconf username, and password, and update push_data.db"""
    data = request.get_json() or {}
    path_name = data.get('path_name')
    interfaces = data.get('interfaces', {})  # {router_name: interface}
    netconf_username = data.get('netconf_username')
    netconf_password = data.get('netconf_password')
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        for router_name, interface in interfaces.items():
            c.execute('''
                UPDATE push_data SET interface_entered_for_push=?, netconf_username=?, netconf_password=?
                WHERE path_name=? AND router_name=?
            ''', (interface, netconf_username, netconf_password, path_name, router_name))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Interfaces and credentials submitted and DB updated'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 

@configuration_push_bp.route('/api/push-data', methods=['GET'])
def get_push_data():
    """Return all rows from push_data table as JSON for UI display"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT path_name, router_name, router_loopback_ip, router_bgp_support_status, interface_entered_for_push, netconf_username, netconf_password FROM push_data')
        rows = c.fetchall()
        conn.close()
        # Convert to list of dicts
        columns = ['path_name', 'router_name', 'router_loopback_ip', 'router_bgp_support_status', 'interface_entered_for_push', 'netconf_username', 'netconf_password']
        data = [dict(zip(columns, row)) for row in rows]
        return jsonify({'success': True, 'rows': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 

@configuration_push_bp.route('/api/push-data-debug', methods=['GET'])
def debug_push_data():
    """Print all rows in push_data table to server console and return as JSON for debugging."""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM push_data')
        rows = c.fetchall()
        conn.close()
        print('DEBUG: push_data table rows:')
        for row in rows:
            print(row)
        return jsonify({'success': True, 'rows': rows})
    except Exception as e:
        print('DEBUG ERROR:', str(e))
        return jsonify({'success': False, 'error': str(e)}) 

@configuration_push_bp.route('/api/select-path', methods=['POST'])
def select_path():
    """Populate push_data only for the selected path, using loopback if available. Clear all previous entries."""
    data = request.get_json()
    path_name = data.get('path_name')
    # Find the path in paths_data
    path = next((p for p in paths_data if p['name'] == path_name), None)
    if not path:
        return jsonify({'success': False, 'error': 'Path not found'}), 404

    routers = path['routers']
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Remove all previous entries (clear table)
        c.execute('DELETE FROM push_data')
        for router_name, router_info in routers.items():
            loopback_ip = get_loopback(router_name) or router_info.get('ip')
            c.execute('''
                INSERT INTO push_data (path_name, router_name, router_loopback_ip)
                VALUES (?, ?, ?)
            ''', (path_name, router_name, loopback_ip))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 

@configuration_push_bp.route('/vpn-services')
def vpn_services():
    return render_template('l3vpn/vpn_services.html') 

@configuration_push_bp.route('/api/vrf-details', methods=['POST'])
def api_vrf_details():
    data = request.get_json()
    try:
        init_vrf_db()
        clear_vrf_db()
        populate_vrf_db(
            vrf_name=data.get('vrf_name'),
            rd=data.get('rd'),
            rt=data.get('rt'),
            description=data.get('description'),
            username=data.get('username'),
            password=data.get('password')
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@configuration_push_bp.route('/api/vrf-table', methods=['GET'])
def api_vrf_table():
    try:
        init_vrf_db()
        rows = fetch_all_vrf_rows()
        return jsonify({'success': True, 'rows': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 

@configuration_push_bp.route('/api/push-vrf', methods=['POST'])
def api_push_vrf():
    import sqlite3
    import os
    VRF_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'vrf.db')
    results = []
    try:
        conn = sqlite3.connect(VRF_DB_PATH)
        c = conn.cursor()
        c.execute('SELECT router_name, router_loopback_ip, vrf_name, rd, rt, description, netconf_username, netconf_password FROM vrf')
        rows = c.fetchall()
        conn.close()
        for row in rows:
            router_name, host, vrf_name, rd, rt, description, username, password = row
            route_targets = [rt_part.strip() for rt_part in rt.split() if rt_part.strip()]
            try:
                mgr = WebVRFManager(host, 830, username, password)
                if mgr.connect():
                    print(f"\n🔄 Pushing VRF config to {host}...")
                    result = mgr.create_vrf(vrf_name, rd, route_targets, description)
                    results.append({'router': router_name, 'success': result.get('success', False), 'message': result.get('device_response', '')})
                mgr.close()
            except Exception as e:
                results.append({'router': router_name, 'success': False, 'message': str(e)})
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}) 