from flask import Blueprint, render_template, request, jsonify
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pathfinder.valid import validate_ip_and_subnet
from pathfinder.find import find_source_and_dest_info
from pathfinder.path import find_paths, build_hop_info

pathfinder_bp = Blueprint('pathfinder', __name__)

@pathfinder_bp.route('/pathfinder')
def pathfinder():
    return render_template('pathfinder/pathfinder.html')

@pathfinder_bp.route('/pathfinder/validate', methods=['POST'])
def pathfinder_validate():
    data = request.json
    src_ip = data.get('src_ip')
    src_mask = data.get('src_mask')
    dst_ip = data.get('dst_ip')
    dst_mask = data.get('dst_mask')
    src_valid, src_msg = validate_ip_and_subnet(src_ip, src_mask)
    dst_valid, dst_msg = validate_ip_and_subnet(dst_ip, dst_mask)
    return jsonify({
        'src_valid': src_valid,
        'src_msg': src_msg,
        'dst_valid': dst_valid,
        'dst_msg': dst_msg
    })

@pathfinder_bp.route('/pathfinder/find', methods=['POST'])
def pathfinder_find():
    data = request.json
    src_ip = data.get('src_ip')
    dst_ip = data.get('dst_ip')
    result = find_source_and_dest_info(src_ip, dst_ip)
    return jsonify(result)

@pathfinder_bp.route('/pathfinder/pathvis', methods=['POST'])
def pathfinder_pathvis():
    data = request.json
    src_ip = data.get('src_ip')
    dst_ip = data.get('dst_ip')
    result = find_paths(src_ip, dst_ip)
    if not result['primary_path']:
        return jsonify({'error': 'No path found.'})
    # Helper to build vis.js nodes/edges for a path
    def build_vis_path(hops):
        nodes = []
        edges = []
        for idx, hop in enumerate(hops):
            router = hop['router_name']
            info_lines = []
            info_lines.append(f"Router Name: {router}")
            if hop.get('entry_interface'):
                info_lines.append(f"Entry Interface: {hop.get('entry_interface')}")
            if hop.get('entry_ip'):
                info_lines.append(f"Entry IP: {hop.get('entry_ip')}")
            if hop.get('exit_interface'):
                info_lines.append(f"Exit Interface: {hop.get('exit_interface')}")
            if hop.get('exit_ip'):
                info_lines.append(f"Exit IP: {hop.get('exit_ip')}")
            if hop.get('loopback'):
                info_lines.append(f"Loopback: {hop.get('loopback')}")
            if hop.get('connection_type'):
                info_lines.append(f"Connection Type: {hop.get('connection_type')}")
            nodes.append({
                'id': router,
                'label': router,
                'info': info_lines
            })
            if idx > 0:
                prev_router = hops[idx-1]['router_name']
                edges.append({'from': prev_router, 'to': router})
        return {'nodes': nodes, 'edges': edges}
    # Build all paths: primary first, then alternates
    primary_hops = build_hop_info(result['primary_path'])
    alternate_hops = [build_hop_info(p) for p in result['alternates']]
    paths = [build_vis_path(primary_hops)] + [build_vis_path(h) for h in alternate_hops]
    return jsonify({'paths': paths}) 