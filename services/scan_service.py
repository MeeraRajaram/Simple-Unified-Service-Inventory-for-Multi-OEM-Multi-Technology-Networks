"""
services/scan_service.py
-----------------------
Subnet scanning and alive IP detection utilities for network automation web app.
Provides functions to parse subnets, ping hosts, and detect live IPs in a given subnet.
"""

import sys
import os
#sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../day17/modules')))
#from subnet_parser import SubnetParser
#from iipinger import IPPinger
#from live_ip_detector import LiveIPDetector
from services.subnet_parser import SubnetParser
from services.iipinger import IPPinger
from services.live_ip_detector import LiveIPDetector

def get_alive_ips(ip, cidr):
    """
    Get a list of alive IP addresses in a given subnet.

    Args:
        ip (str): An IP address within the subnet (not used in logic, but may be for future extension).
        cidr (str): Subnet in CIDR notation (e.g., '192.168.1.0/24').
    Returns:
        list: List of alive IP addresses in the subnet.
    """
    # Parse subnet to get all host IPs
    parser = SubnetParser()
    subnet_result = parser.parse_subnet(cidr)
    if not subnet_result['is_valid']:
        return []
    host_ips = subnet_result['host_ips']
    # Ping all IPs in subnet
    pinger = IPPinger(timeout=1.5)
    ping_results = pinger.ping_subnet(host_ips)
    # Confirm live IPs
    detector = LiveIPDetector(timeout=2.0)
    detection_results = detector.confirm_live_ips(ping_results)
    live_ips = detector.get_confirmed_live_ips(detection_results)
    return live_ips 