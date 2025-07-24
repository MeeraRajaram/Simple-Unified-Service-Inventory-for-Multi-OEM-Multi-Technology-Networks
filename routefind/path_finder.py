"""
routefind/path_finder.py
-----------------------
Path finding algorithms and network topology analysis for network automation web app.
Provides functions to build network links, convert to graph representation, and find primary/alternate paths between routers.
"""

import ipaddress
import heapq
from collections import defaultdict

def build_links(routers):
    """
    Build network links from router information.

    Args:
        routers (dict): Dictionary of router information.
    Returns:
        set: Set of link tuples (router1, iface1, ip1, router2, iface2, ip2, subnet).
    """
    links = set()
    router_list = list(routers.values())
    for i, r1 in enumerate(router_list):
        for iface1, data1 in r1['interfaces'].items():
            subnet1 = data1['subnet']
            ip1 = data1['ip']
            if not subnet1 or not ip1:
                continue
            net1 = ipaddress.ip_network(subnet1, strict=False)
            for j, r2 in enumerate(router_list):
                if r1['loopback'] == r2['loopback']:
                    continue
                for iface2, data2 in r2['interfaces'].items():
                    subnet2 = data2['subnet']
                    ip2 = data2['ip']
                    if not subnet2 or not ip2:
                        continue
                    net2 = ipaddress.ip_network(subnet2, strict=False)
                    if net1 == net2:
                        link_key = (r1['name'], iface1, ip1, r2['name'], iface2, ip2, str(net1))
                        if link_key not in links:
                            links.add(link_key)
    return links

def build_graph(links):
    """
    Convert network links to graph representation.

    Args:
        links (set): Set of network links.
    Returns:
        tuple: (graph dict, link_info dict).
    """
    graph = defaultdict(list)
    link_info = {}
    for r1, iface1, ip1, r2, iface2, ip2, subnet in links:
        graph[r1].append(r2)
        graph[r2].append(r1)
        link_info[(r1, r2)] = (iface1, ip1, iface2, ip2, subnet)
        link_info[(r2, r1)] = (iface2, ip2, iface1, ip1, subnet)
    return dict(graph), link_info

def find_paths(graph, start, goal, max_paths=2):
    """
    Find multiple paths between start and goal nodes using modified Dijkstra's algorithm.

    Args:
        graph (dict): Network graph representation.
        start (str): Start router name.
        goal (str): Goal router name.
        max_paths (int): Maximum number of paths to find.
    Returns:
        list: List of paths, each path is a list of router names, labeled as ('Primary', path) or ('Alternate', path).
    """
    paths = []
    visited = set()
    def find_path():
        queue = [(0, start, [start])]
        path_visited = set()
        while queue:
            cost, node, path = heapq.heappop(queue)
            if node == goal:
                return path
            if node in path_visited:
                continue
            path_visited.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in path_visited and (node, neighbor) not in visited:
                    heapq.heappush(queue, (cost + 1, neighbor, path + [neighbor]))
        return None
    # Find primary path
    primary_path = find_path()
    if primary_path:
        paths.append(('Primary', primary_path))
        # Mark primary path edges as visited to find alternate paths
        for i in range(len(primary_path) - 1):
            visited.add((primary_path[i], primary_path[i+1]))
            visited.add((primary_path[i+1], primary_path[i]))
        # Find alternate path
        alternate_path = find_path()
        if alternate_path:
            paths.append(('Alternate', alternate_path))
    return paths 