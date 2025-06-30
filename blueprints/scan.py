from flask import Blueprint, render_template, session
from services.scan_service import get_alive_ips

scan_bp = Blueprint('scan', __name__)

@scan_bp.route('/alive_ips', methods=['GET'])
def alive_ips():
    ip = session.get('ip')
    cidr = session.get('cidr')
    alive_ips = get_alive_ips(ip, cidr)
    return render_template('alive_ips.html', ip=ip, cidr=cidr, alive_ips=alive_ips) 