from flask import render_template, request, flash, redirect, url_for
from routefind import bp
from routefind.ip_validator import is_valid_ip
from routefind.router_finder import find_source_and_dest_routers, find_router_for_ip

@bp.route('/routefind', methods=['GET', 'POST'])
def find_route():
    if request.method == 'POST':
        source_ip = request.form.get('source_ip')
        dest_ip = request.form.get('dest_ip')
        # Validate IPs
        if not is_valid_ip(source_ip):
            flash('Invalid source IP address.', 'danger')
            return redirect(url_for('routefind.find_route'))
        if not is_valid_ip(dest_ip):
            flash('Invalid destination IP address.', 'danger')
            return redirect(url_for('routefind.find_route'))
        # Lookup routers
        result = find_source_and_dest_routers(source_ip, dest_ip)
        return render_template('routefind/lookup_result.html', source_ip=source_ip, dest_ip=dest_ip, result=result)
    return render_template('routefind/index.html')

@bp.route('/find-router', methods=['GET', 'POST'])
def find_router():
    if request.method == 'POST':
        ip_address = request.form.get('ip_address')
        if not is_valid_ip(ip_address):
            flash('Invalid IP address.', 'danger')
            return redirect(url_for('routefind.find_router'))
        result = find_router_for_ip(ip_address)
        return render_template('routefind/router_result.html', ip_address=ip_address, result=result)
    return render_template('routefind/find_router.html') 