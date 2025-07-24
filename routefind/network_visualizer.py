"""
routefind/network_visualizer.py
------------------------------
Network topology visualization utilities for network automation web app.
Provides functions to generate node positions and visualization data for web-based network topology and path displays.
"""

import math
import json

def generate_network_layout(routers, paths):
    """
    Generate layout positions for network visualization.

    Args:
        routers (list): List of router names.
        paths (list): List of paths to highlight.
    Returns:
        dict: Node positions and visualization data.
    """
    positions = {}
    center_x, center_y = 500, 300
    radius = min(200, 2000 // len(routers))
    # Position all routers in a circle
    for i, router in enumerate(routers):
        angle = 2 * math.pi * i / len(routers)
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        positions[router] = {'x': x, 'y': y}
    return positions

def create_path_visualization(positions, paths, link_info):
    """
    Create visualization data for network paths.

    Args:
        positions (dict): Router positions.
        paths (list): List of paths (primary and alternate).
        link_info (dict): Link information between routers.
    Returns:
        dict: Visualization data for the web interface.
    """
    visualization_data = {
        'nodes': [],
        'links': [],
        'paths': []
    }
    # Add nodes
    for router, pos in positions.items():
        visualization_data['nodes'].append({
            'id': router,
            'x': pos['x'],
            'y': pos['y'],
            'label': router
        })
    # Add paths and links
    for path_type, path in paths:
        path_links = []
        for i in range(len(path) - 1):
            r1, r2 = path[i], path[i + 1]
            iface1, ip1, iface2, ip2, subnet = link_info.get((r1, r2), ('', '', '', '', ''))
            link = {
                'source': r1,
                'target': r2,
                'sourceInterface': iface1,
                'targetInterface': iface2,
                'sourceIP': ip1,
                'targetIP': ip2,
                'subnet': subnet,
                'type': path_type.lower()
            }
            path_links.append(link)
        visualization_data['paths'].append({
            'type': path_type,
            'routers': path,
            'links': path_links
        })
        # Add links to main links list
        visualization_data['links'].extend(path_links)
    return visualization_data

def generate_visualization_json(routers, paths, link_info):
    """
    Generate complete visualization JSON for the web interface.

    Args:
        routers (list): List of router names.
        paths (list): List of paths.
        link_info (dict): Link information.
    Returns:
        str: JSON string with visualization data.
    """
    positions = generate_network_layout(routers, paths)
    vis_data = create_path_visualization(positions, paths, link_info)
    return json.dumps(vis_data) 