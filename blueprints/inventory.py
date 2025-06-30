from flask import Blueprint, render_template, request, flash, session
from services.inventory_service import validate_ip_and_cidr
from services.scan_service import get_alive_ips
from services.netconf_service import check_netconf_for_ips
from services.db import router_db

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory', methods=['GET', 'POST'])
def inventory():
    alive_ips = []
    ip = session.get('ip')
    cidr = session.get('cidr')
    credentials = {}
    netconf_results = []
    if request.method == 'POST':
        ip = request.form.get('ip')
        cidr = request.form.get('cidr')
        # If credentials are being submitted
        if request.form.get('submit_credentials'):
            # Get alive IPs from session or re-scan
            alive_ips = get_alive_ips(ip, cidr)
            ip_cred_list = []
            for aip in alive_ips:
                username = request.form.get(f'username_{aip}', '')
                password = request.form.get(f'password_{aip}', '')
                ip_cred_list.append({'ip': aip, 'username': username, 'password': password})
            netconf_results = check_netconf_for_ips(ip_cred_list)
            # Store only successful routers in the database
            for dev in netconf_results:
                if dev['netconf_status'].startswith('Enabled'):
                    router_db.add_router(dev['hostname'], dev['software_version'], dev['ip'], dev['vendor'], dev['username'], dev['password'])
            return render_template('inventory.html', ip=ip, cidr=cidr, alive_ips=alive_ips, credentials=credentials, netconf_results=netconf_results)
        # Otherwise, it's the initial IP/CIDR validation and scan
        validation = validate_ip_and_cidr(ip, cidr)
        if not validation['is_valid']:
            flash(f"Invalid IP or not in subnet: {validation['error']}", 'error')
            return render_template('inventory.html', ip=ip, cidr=cidr, alive_ips=[], credentials={}, netconf_results=[])
        session['ip'] = ip
        session['cidr'] = cidr
        alive_ips = get_alive_ips(ip, cidr)
        credentials = {ip: {'username': '', 'password': ''} for ip in alive_ips}
        return render_template('inventory.html', ip=ip, cidr=cidr, alive_ips=alive_ips, credentials=credentials, netconf_results=[])
    # GET: show form, and if session has ip/cidr, show alive IPs
    if ip and cidr:
        alive_ips = get_alive_ips(ip, cidr)
        credentials = {ip: {'username': '', 'password': ''} for ip in alive_ips}
    return render_template('inventory.html', ip=ip, cidr=cidr, alive_ips=alive_ips, credentials=credentials, netconf_results=netconf_results) 