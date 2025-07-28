#!/usr/bin/env python3
"""
IP Validator Module

This module validates IP addresses within specified subnets and identifies
special addresses like network, broadcast, first/last usable hosts.

Author: IP Scanner Automation System
"""

import ipaddress
from typing import Dict, List, Tuple, Optional


class IPValidator:
    """Validates IP addresses and provides detailed information about their role in subnets."""
    
    def __init__(self):
        self.validation_results = {}
    
    def validate_ip_in_subnet(self, ip: str, subnet: str) -> Dict:
        """
        Validates if an IP address is within the specified subnet.
        
        Args:
            ip (str): IP address to validate (e.g., "192.168.1.1")
            subnet (str): Subnet in CIDR notation (e.g., "192.168.1.0/24")
            
        Returns:
            Dict: Validation results with status and details
        """
        try:
            # Parse the IP and subnet
            ip_obj = ipaddress.IPv4Address(ip)
            network = ipaddress.IPv4Network(subnet, strict=False)
            
            # Check if IP is in the network
            is_in_network = ip_obj in network
            
            # Determine the role of the IP
            role = self._determine_ip_role(ip_obj, network)
            
            # Get network information
            network_info = {
                'network_address': str(network.network_address),
                'broadcast_address': str(network.broadcast_address),
                'first_usable_host': str(network.network_address + 1),
                'last_usable_host': str(network.broadcast_address - 1),
                'total_hosts': network.num_addresses - 2,  # Exclude network and broadcast
                'subnet_mask': str(network.netmask),
                'prefix_length': network.prefixlen
            }
            
            return {
                'ip': ip,
                'subnet': subnet,
                'is_valid': is_in_network,
                'role': role,
                'network_info': network_info,
                'error': None
            }
            
        except ValueError as e:
            return {
                'ip': ip,
                'subnet': subnet,
                'is_valid': False,
                'role': 'invalid',
                'network_info': None,
                'error': str(e)
            }
    
    def _determine_ip_role(self, ip_obj: ipaddress.IPv4Address, network: ipaddress.IPv4Network) -> str:
        """
        Determines the role of an IP address within a network.
        
        Args:
            ip_obj: IPv4Address object
            network: IPv4Network object
            
        Returns:
            str: Role description
        """
        if ip_obj == network.network_address:
            return "Network Address"
        elif ip_obj == network.broadcast_address:
            return "Broadcast Address"
        elif ip_obj == network.network_address + 1:
            return "First Usable Host"
        elif ip_obj == network.broadcast_address - 1:
            return "Last Usable Host"
        else:
            return "Usable Host"
    
    def validate_source_destination(self, source_ip: str, source_subnet: str, 
                                  destination_ip: str, destination_subnet: str) -> Dict:
        """
        Validates source and destination IP/subnet combinations.
        
        Args:
            source_ip (str): Source IP address
            source_subnet (str): Source subnet in CIDR notation
            destination_ip (str): Destination IP address
            destination_subnet (str): Destination subnet in CIDR notation
            
        Returns:
            Dict: Comprehensive validation results
        """
        source_validation = self.validate_ip_in_subnet(source_ip, source_subnet)
        dest_validation = self.validate_ip_in_subnet(destination_ip, destination_subnet)
        
        # Check for common issues
        warnings = []
        
        if source_validation['role'] in ['Network Address', 'Broadcast Address']:
            warnings.append(f"Source IP {source_ip} is a {source_validation['role']} in {source_subnet}")
        
        if dest_validation['role'] in ['Network Address', 'Broadcast Address']:
            warnings.append(f"Destination IP {destination_ip} is a {dest_validation['role']} in {destination_subnet}")
        
        # Check if source and destination are in the same subnet
        try:
            source_network = ipaddress.IPv4Network(source_subnet, strict=False)
            dest_network = ipaddress.IPv4Network(destination_subnet, strict=False)
            
            if source_network == dest_network:
                warnings.append("Source and destination are in the same subnet")
            elif source_network.overlaps(dest_network):
                warnings.append("Source and destination subnets overlap")
                
        except ValueError:
            pass
        
        return {
            'source': source_validation,
            'destination': dest_validation,
            'warnings': warnings,
            'overall_valid': source_validation['is_valid'] and dest_validation['is_valid']
        }
    
    def get_available_subnets(self) -> List[str]:
        """
        Returns a list of commonly used subnet prefixes.
        
        Returns:
            List[str]: List of subnet prefixes
        """
        return ['/30', '/29', '/28', '/27', '/26', '/25', '/24', '/23', '/22', '/21', '/20', '/16', '/8']
    
    def format_validation_output(self, validation_result: Dict) -> str:
        """
        Formats validation results into a user-friendly string.
        
        Args:
            validation_result (Dict): Validation result from validate_source_destination
            
        Returns:
            str: Formatted output string
        """
        output = []
        
        # Source validation
        source = validation_result['source']
        output.append(f"Source IP: {source['ip']}")
        output.append(f"Source Subnet: {source['subnet']}")
        output.append(f"Status: {'✓ Valid' if source['is_valid'] else '✗ Invalid'}")
        if source['is_valid']:
            output.append(f"Role: {source['role']}")
        if source['error']:
            output.append(f"Error: {source['error']}")
        
        output.append("")
        
        # Destination validation
        dest = validation_result['destination']
        output.append(f"Destination IP: {dest['ip']}")
        output.append(f"Destination Subnet: {dest['subnet']}")
        output.append(f"Status: {'✓ Valid' if dest['is_valid'] else '✗ Invalid'}")
        if dest['is_valid']:
            output.append(f"Role: {dest['role']}")
        if dest['error']:
            output.append(f"Error: {dest['error']}")
        
        # Warnings
        if validation_result['warnings']:
            output.append("")
            output.append("⚠️  Warnings:")
            for warning in validation_result['warnings']:
                output.append(f"  - {warning}")
        
        # Overall status
        output.append("")
        overall_status = "✓ All validations passed" if validation_result['overall_valid'] else "✗ Validation failed"
        output.append(f"Overall Status: {overall_status}")
        
        return "\n".join(output)


def main():
    """Test function for the IP validator module."""
    validator = IPValidator()
    
    # Test cases
    test_cases = [
        {
            'source_ip': '192.168.1.1',
            'source_subnet': '192.168.1.0/24',
            'destination_ip': '192.168.2.1',
            'destination_subnet': '192.168.2.0/24'
        },
        {
            'source_ip': '192.168.1.0',
            'source_subnet': '192.168.1.0/24',
            'destination_ip': '192.168.1.255',
            'destination_subnet': '192.168.1.0/24'
        },
        {
            'source_ip': '10.0.0.1',
            'source_subnet': '10.0.0.0/30',
            'destination_ip': '10.0.0.2',
            'destination_subnet': '10.0.0.0/30'
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== Test Case {i} ===")
        result = validator.validate_source_destination(
            test_case['source_ip'], test_case['source_subnet'],
            test_case['destination_ip'], test_case['destination_subnet']
        )
        print(validator.format_validation_output(result))


if __name__ == "__main__":
    main() 