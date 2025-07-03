import ipaddress

def validate_ip_and_subnet(ip_str, subnet_str):
    try:
        # Parse subnet (e.g., '/24' -> 24)
        if subnet_str.startswith('/'):
            prefixlen = int(subnet_str[1:])
        else:
            prefixlen = int(subnet_str)
        # Build network
        network = ipaddress.ip_network(f'{ip_str}/{prefixlen}', strict=False)
        ip = ipaddress.ip_address(ip_str)
        # Check if IP is in network
        if ip not in network:
            return False, f"IP {ip_str} is not in the subnet {network}" 
        # Check if network or broadcast
        if ip == network.network_address:
            return False, f"{ip_str} is the network address of {network}" 
        if ip == network.broadcast_address:
            return False, f"{ip_str} is the broadcast address of {network}" 
        return True, f"{ip_str} is a valid host IP in {network}"
    except ValueError as e:
        return False, f"Invalid input: {e}" 