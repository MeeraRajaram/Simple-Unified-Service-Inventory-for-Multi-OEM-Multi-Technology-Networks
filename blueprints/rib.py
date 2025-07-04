from flask import Blueprint, render_template, redirect, url_for, request
from rib.db_utils import rib_db_manage
from rib.db_parser import parse_and_dispatch
from topo.topo_inip import build_and_store_inip_table
from topo.topo_connections import process_and_save_connections

rib_bp = Blueprint('rib', __name__)
 
@rib_bp.route('/rib', methods=['GET'])
def rib():
    entries = rib_db_manage.get_entries()
    return render_template('rib/rib.html', entries=entries)

@rib_bp.route('/rib/refresh', methods=['POST'])
def rib_refresh():
    # Save current RIB to history before clearing
    if rib_db_manage.get_entries():
        rib_db_manage.save_rib_to_history()
    rib_db_manage.clear()  # Clear the RIB table before each scan
    parse_and_dispatch()   # This will scan all routers and update the RIB table
    build_and_store_inip_table()  # Repopulate inip.db from RIB
    process_and_save_connections()  # Repopulate directconndb and protodb from RIB
    return redirect(url_for('rib.rib'))

@rib_bp.route('/rib/history', methods=['GET'])
def rib_history():
    drafts = rib_db_manage.get_history_drafts()
    history_tables = []
    for draft_name, timestamp in drafts:
        entries = rib_db_manage.get_history_entries(draft_name)
        history_tables.append({
            'draft_name': draft_name,
            'timestamp': timestamp,
            'entries': entries
        })
    return render_template('rib/rib_history.html', history_tables=history_tables) 