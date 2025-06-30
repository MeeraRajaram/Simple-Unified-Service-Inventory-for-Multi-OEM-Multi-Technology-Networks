"""
Blueprint: routefind.py
Purpose: Handles route finding functionality and visualization in the web interface.
"""

from flask import Blueprint, render_template, request, jsonify, flash
from routefind.ip_validator import is_valid_ip, validate_ip_with_subnet
from routefind.router_finder import find_router_for_ip, get_router_info
from routefind.path_finder import build_links, build_graph, find_paths
from routefind.network_visualizer import generate_visualization_json

routefind_bp = Blueprint('routefind', __name__)

@routefind_bp.route('/routefind', methods=['GET', 'POST'])
def find_route():
    if request.method == 'POST':
        source_ip = request.form.get('source')
        source_subnet = request.form.get('source_subnet')
        dest_ip = request.form.get('destination')
        dest_subnet = request.form.get('destination_subnet')
        
        # Validate inputs
        if not all([source_ip, source_subnet, dest_ip, dest_subnet]):
            flash('Please provide all required information', 'error')
            return render_template('routefind/index.html')
        
        # Validate source IP and subnet
        is_valid_source, source_msg = validate_ip_with_subnet(source_ip, source_subnet)
        if not is_valid_source:
            flash(f'Source IP error: {source_msg}', 'error')
            return render_template('routefind/index.html')
            
        # Validate destination IP and subnet
        is_valid_dest, dest_msg = validate_ip_with_subnet(dest_ip, dest_subnet)
        if not is_valid_dest:
            flash(f'Destination IP error: {dest_msg}', 'error')
            return render_template('routefind/index.html')
        
        try:
            # Get router information
            routers = {}
            
            # Get source router info
            source_router = get_router_info(source_ip)
            if not source_router:
                flash(f'Could not find source router for IP: {source_ip}', 'error')
                return render_template('routefind/index.html')
            routers[source_ip] = source_router
            
            # Get destination router info
            dest_router = get_router_info(dest_ip)
            if not dest_router:
                flash(f'Could not find destination router for IP: {dest_ip}', 'error')
                return render_template('routefind/index.html')
            routers[dest_ip] = dest_router
            
            # Build network topology
            links = build_links(routers)
            graph, link_info = build_graph(links)
            
            # Find paths
            paths = find_paths(graph, source_router['name'], dest_router['name'])
            
            if not paths:
                flash('No path found between the specified routers', 'warning')
                return render_template('routefind/index.html',
                                    source_router=source_router,
                                    dest_router=dest_router)
            
            # Generate visualization data
            vis_data = generate_visualization_json(list(graph.keys()), paths, link_info)
            
            return render_template('routefind/index.html',
                                source_router=source_router,
                                dest_router=dest_router,
                                paths=paths,
                                visualization_data=vis_data)
            
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
            return render_template('routefind/index.html')
    
    return render_template('routefind/index.html') 