from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from services.gns3_service import connect_to_gns3
from services.db import router_db
from services.netconf_service import check_netconf_for_ips

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        gns3_url = request.form.get('gns3_url')
        project_name = request.form.get('project_name')
        success, message = connect_to_gns3(gns3_url, project_name)
        flash(message, 'info' if success else 'error')
        if success:
            session['gns3_url'] = gns3_url
            session['project_name'] = project_name
            return redirect(url_for('inventory.inventory'))
        return redirect(url_for('main.index'))
    return render_template('index.html')

@main_bp.route('/routers', methods=['GET'])
def show_routers():
    routers = router_db.get_latest_routers()
    return render_template('routers.html', routers=routers)

@main_bp.route('/show-database', methods=['GET'])
def show_database():
    routers = router_db.get_routers()
    ip_cred_list = [
        {'ip': ip, 'username': username, 'password': password}
        for _, _, ip, _, username, password in routers
    ]
    results = check_netconf_for_ips(ip_cred_list)
    return jsonify(results)

@main_bp.route('/end_connection', methods=['POST'])
def end_connection():
    router_db.clear()
    flash('Router database cleared.', 'info')
    return redirect(url_for('main.index')) 