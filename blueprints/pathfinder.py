from flask import Blueprint, render_template, request, jsonify
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pathfinder.valid import validate_ip_and_subnet
from pathfinder.find import find_source_and_dest_info
from pathfinder.path import find_paths

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
    if not result['primary']:
        return jsonify({'error': 'No path found.'})
    # Helper to build vis.js nodes/edges for a path
    def build_vis_path(path):
        nodes = []
        edges = []
        for idx, hop in enumerate(path):
            router = hop['router_name']
            node_id = idx
            info_lines = []
            if idx == 0:
                info_lines.append(f"Source IP: {hop.get('entry_ip','')}")
                info_lines.append(f"Source IP Interface: {hop.get('entry_interface','')}")
                info_lines.append(f"Exit Interface: {hop.get('exit_interface','')}")
                info_lines.append(f"Exit Interface IP: {hop.get('exit_ip','')}")
                info_lines.append(f"Loopback: {hop.get('loopback','')}")
            elif idx == len(path)-1:
                info_lines.append(f"Destination IP: {hop.get('entry_ip','')}")
                info_lines.append(f"Destination IP Interface: {hop.get('entry_interface','')}")
                info_lines.append(f"Entry Interface: {hop.get('entry_interface','')}")
                info_lines.append(f"Entry Interface IP: {hop.get('entry_ip','')}")
                info_lines.append(f"Loopback: {hop.get('loopback','')}")
            else:
                info_lines.append(f"Router Name: {router}")
                info_lines.append(f"Entry Interface: {hop.get('entry_interface','')}")
                info_lines.append(f"Entry Interface IP: {hop.get('entry_ip','')}")
                info_lines.append(f"Exit Interface: {hop.get('exit_interface','')}")
                info_lines.append(f"Exit Interface IP: {hop.get('exit_ip','')}")
                info_lines.append(f"Loopback: {hop.get('loopback','')}")
            nodes.append({
                'id': node_id,
                'label': router,
                'info': info_lines
            })
        for idx in range(len(path)-1):
            from_id = idx
            to_id = idx+1
            conn_type = path[idx]['connection_type'] or ''
            edges.append({
                'from': from_id,
                'to': to_id,
                'label': conn_type
            })
        return {'nodes': nodes, 'edges': edges}
    # Build all paths: primary first, then alternates
    paths = [build_vis_path(p) for p in [result['primary'][0]] + result['alternates']]
    return jsonify({'paths': paths}) 