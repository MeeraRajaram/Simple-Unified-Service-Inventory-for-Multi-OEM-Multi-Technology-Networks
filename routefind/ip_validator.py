"""
routefind/ip_validator.py
------------------------
IP address validation utilities for network automation web app.
Provides functions to validate IP addresses and check if an IP belongs to a given subnet, excluding network/broadcast addresses.
"""

import ipaddress

def is_valid_ip(ip):
    """
    Check if a given string is a valid IP address.

    Args:
        ip (str): IP address to validate.
    Returns:
        bool: True if valid IP, False otherwise.
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def validate_ip_with_subnet(ip, subnet):
    """
    Validate if an IP address belongs to a subnet range and is not network/broadcast address.

    Args:
        ip (str): IP address to validate.
        subnet (str): Subnet in CIDR notation (e.g., "192.168.1.0/24").
    Returns:
        tuple: (bool, str) - (is_valid, message).
    """
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj in network:
            if ip_obj != network.network_address and ip_obj != network.broadcast_address:
                return True, "Valid IP for the given subnet"
            else:
                return False, "IP cannot be network address or broadcast address"
        else:
            return False, "IP is not within the subnet range"
    except ValueError as e:
        return False, f"Invalid IP or subnet format: {str(e)}" 