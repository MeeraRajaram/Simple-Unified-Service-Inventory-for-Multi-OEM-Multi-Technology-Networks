#!/usr/bin/env python3
"""
Subnet Parser Module

This module parses CIDR notation subnets and expands them into lists of
valid host IP addresses, excluding network and broadcast addresses.

Author: IP Scanner Automation System
"""

import ipaddress
from typing import List, Dict, Optional


class SubnetParser:
    """Parses and expands CIDR notation subnets into host IP lists."""
    
    def __init__(self):
        self.parsed_subnets = {}
    
    def parse_subnet(self, subnet: str) -> Dict:
        """
        Parses a subnet in CIDR notation and returns detailed information.
        
        Args:
            subnet (str): Subnet in CIDR notation (e.g., "192.168.1.0/24")
            
        Returns:
            Dict: Parsed subnet information including host IPs
        """
        try:
            # Parse the network
            network = ipaddress.IPv4Network(subnet, strict=False)
            
            # Generate list of host IPs (excluding network and broadcast)
            host_ips = []
            for ip in network.hosts():
                host_ips.append(str(ip))
            
            # Calculate network information
            network_info = {
                'network_address': str(network.network_address),
                'broadcast_address': str(network.broadcast_address),
                'subnet_mask': str(network.netmask),
                'prefix_length': network.prefixlen,
                'total_addresses': network.num_addresses,
                'usable_hosts': network.num_addresses - 2,
                'first_host': str(network.network_address + 1),
                'last_host': str(network.broadcast_address - 1)
            }
            
            result = {
                'subnet': subnet,
                'host_ips': host_ips,
                'network_info': network_info,
                'is_valid': True,
                'error': None
            }
            
            # Store for caching
            self.parsed_subnets[subnet] = result
            
            return result
            
        except ValueError as e:
            return {
                'subnet': subnet,
                'host_ips': [],
                'network_info': None,
                'is_valid': False,
                'error': str(e)
            }
    
    def get_host_ips(self, subnet: str) -> List[str]:
        """
        Gets only the list of host IPs for a given subnet.
        
        Args:
            subnet (str): Subnet in CIDR notation
            
        Returns:
            List[str]: List of host IP addresses
        """
        result = self.parse_subnet(subnet)
        return result['host_ips'] if result['is_valid'] else []
    
    def parse_multiple_subnets(self, subnets: List[str]) -> Dict[str, Dict]:
        """
        Parses multiple subnets and returns results for each.
        
        Args:
            subnets (List[str]): List of subnets in CIDR notation
            
        Returns:
            Dict[str, Dict]: Dictionary mapping subnet to parse results
        """
        results = {}
        for subnet in subnets:
            results[subnet] = self.parse_subnet(subnet)
        return results
    
    def get_subnet_summary(self, subnet: str) -> str:
        """
        Returns a human-readable summary of the subnet.
        
        Args:
            subnet (str): Subnet in CIDR notation
            
        Returns:
            str: Formatted summary string
        """
        result = self.parse_subnet(subnet)
        
        if not result['is_valid']:
            return f"Invalid subnet: {result['error']}"
        
        info = result['network_info']
        return (
            f"Subnet: {subnet}\n"
            f"Network Address: {info['network_address']}\n"
            f"Broadcast Address: {info['broadcast_address']}\n"
            f"Subnet Mask: {info['subnet_mask']}\n"
            f"Total Addresses: {info['total_addresses']}\n"
            f"Usable Hosts: {info['usable_hosts']}\n"
            f"First Host: {info['first_host']}\n"
            f"Last Host: {info['last_host']}"
        )
    
    def validate_subnet_format(self, subnet: str) -> bool:
        """
        Validates if a string is in valid CIDR notation.
        
        Args:
            subnet (str): Subnet string to validate
            
        Returns:
            bool: True if valid CIDR notation
        """
        try:
            ipaddress.IPv4Network(subnet, strict=False)
            return True
        except ValueError:
            return False
    
    def get_common_subnets(self) -> List[str]:
        """
        Returns a list of commonly used subnet prefixes.
        
        Returns:
            List[str]: List of common subnet prefixes
        """
        return [
            '/30',   # 4 addresses, 2 usable (point-to-point)
            '/29',   # 8 addresses, 6 usable
            '/28',   # 16 addresses, 14 usable
            '/27',   # 32 addresses, 30 usable
            '/26',   # 64 addresses, 62 usable
            '/25',   # 128 addresses, 126 usable
            '/24',   # 256 addresses, 254 usable (most common)
            '/23',   # 512 addresses, 510 usable
            '/22',   # 1024 addresses, 1022 usable
            '/21',   # 2048 addresses, 2046 usable
            '/20',   # 4096 addresses, 4094 usable
            '/16',   # 65536 addresses, 65534 usable
            '/8'     # 16777216 addresses, 16777214 usable
        ]
    
    def create_subnet_from_ip(self, ip: str, prefix_length: int) -> str:
        """
        Creates a subnet from an IP address and prefix length.
        
        Args:
            ip (str): IP address
            prefix_length (int): Prefix length (0-32)
            
        Returns:
            str: Subnet in CIDR notation
        """
        try:
            ip_obj = ipaddress.IPv4Address(ip)
            network = ipaddress.IPv4Network(f"{ip}/{prefix_length}", strict=False)
            return str(network)
        except ValueError as e:
            raise ValueError(f"Invalid IP or prefix length: {e}")


def main():
    """Test function for the subnet parser module."""
    parser = SubnetParser()
    
    # Test cases
    test_subnets = [
        "192.168.1.0/24",
        "10.0.0.0/30",
        "172.16.0.0/16",
        "192.168.100.0/25",
        "invalid.subnet.here"
    ]
    
    for subnet in test_subnets:
        print(f"\n=== Testing Subnet: {subnet} ===")
        
        if parser.validate_subnet_format(subnet):
            result = parser.parse_subnet(subnet)
            print(parser.get_subnet_summary(subnet))
            print(f"Number of host IPs: {len(result['host_ips'])}")
            
            # Show first few IPs
            if result['host_ips']:
                print("First 5 host IPs:")
                for ip in result['host_ips'][:5]:
                    print(f"  {ip}")
                if len(result['host_ips']) > 5:
                    print(f"  ... and {len(result['host_ips']) - 5} more")
        else:
            print("Invalid subnet format")


if __name__ == "__main__":
    main() 