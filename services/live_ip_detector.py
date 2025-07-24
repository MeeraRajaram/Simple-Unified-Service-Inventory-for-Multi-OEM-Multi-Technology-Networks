#!/usr/bin/env python3
"""
Live IP Detector Module

This module filters and confirms live IP addresses from ping results.
It also provides fallback methods when ping is blocked or unreliable.

Author: IP Scanner Automation System
"""

import socket
import threading
import time
from typing import List, Dict, Optional
import subprocess
import platform


class LiveIPDetector:
    """Detects and confirms live IP addresses using multiple methods."""
    
    def __init__(self, timeout: float = 2.0, max_threads: int = 50):
        """
        Initialize the live IP detector.
        
        Args:
            timeout (float): Timeout for connection attempts
            max_threads (int): Maximum number of concurrent threads
        """
        self.timeout = timeout
        self.max_threads = max_threads
        self.detection_methods = ['ping', 'tcp_connect', 'arp']
    
    def filter_ping_results(self, ping_results: Dict[str, Dict]) -> List[str]:
        """
        Filters ping results to extract confirmed live IPs.
        
        Args:
            ping_results (Dict[str, Dict]): Results from ping operations
            
        Returns:
            List[str]: List of confirmed live IP addresses
        """
        live_ips = []
        
        for ip, result in ping_results.items():
            if result['alive']:
                # Additional validation: check if response time is reasonable
                if result['response_time'] is None or result['response_time'] < 10000:  # 10 seconds max
                    live_ips.append(ip)
        
        return live_ips
    
    def tcp_connect_scan(self, ips: List[str], ports: List[int] = None) -> Dict[str, bool]:
        """
        Performs TCP connection scan on specified ports.
        
        Args:
            ips (List[str]): List of IP addresses to scan
            ports (List[int]): List of ports to check (default: common ports)
            
        Returns:
            Dict[str, bool]: Dictionary mapping IP to connectivity status
        """
        if ports is None:
            ports = [22, 23, 80, 443, 8080, 8443]  # Common ports
        
        results = {}
        
        def scan_ip_port(ip: str, port: int) -> bool:
            """Attempts TCP connection to IP:port."""
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                result = sock.connect_ex((ip, port))
                sock.close()
                return result == 0
            except Exception:
                return False
        
        for ip in ips:
            # Try multiple ports for each IP
            is_live = False
            for port in ports:
                if scan_ip_port(ip, port):
                    is_live = True
                    break
            results[ip] = is_live
        
        return results
    
    def arp_scan(self, ips: List[str]) -> Dict[str, bool]:
        """
        Performs ARP scan to detect live hosts (Linux/Unix only).
        
        Args:
            ips (List[str]): List of IP addresses to scan
            
        Returns:
            Dict[str, bool]: Dictionary mapping IP to ARP response status
        """
        results = {}
        
        if platform.system().lower() != "linux":
            # ARP scan not available on this platform
            for ip in ips:
                results[ip] = False
            return results
        
        try:
            # Use arping if available
            for ip in ips:
                try:
                    cmd = ["arping", "-c", "1", "-w", str(int(self.timeout)), ip]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout + 1)
                    results[ip] = result.returncode == 0
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    results[ip] = False
        except Exception:
            # Fallback: mark all as not detected
            for ip in ips:
                results[ip] = False
        
        return results
    
    def dns_lookup(self, ips: List[str]) -> Dict[str, bool]:
        """
        Performs reverse DNS lookup to detect hosts with DNS records.
        
        Args:
            ips (List[str]): List of IP addresses to check
            
        Returns:
            Dict[str, bool]: Dictionary mapping IP to DNS record status
        """
        results = {}
        
        def lookup_ip(ip: str) -> bool:
            """Performs reverse DNS lookup for an IP."""
            try:
                hostname = socket.gethostbyaddr(ip)[0]
                return hostname != ip  # Has a proper hostname
            except (socket.herror, socket.gaierror):
                return False
        
        for ip in ips:
            results[ip] = lookup_ip(ip)
        
        return results
    
    def confirm_live_ips(self, ping_results: Dict[str, Dict], 
                        ips: List[str] = None) -> Dict[str, Dict]:
        """
        Confirms live IPs using multiple detection methods.
        
        Args:
            ping_results (Dict[str, Dict]): Results from ping operations
            ips (List[str]): Optional list of IPs to check (if None, uses ping results)
            
        Returns:
            Dict[str, Dict]: Comprehensive detection results
        """
        if ips is None:
            # Use IPs from ping results
            ips = list(ping_results.keys())
        
        # Start with ping results
        ping_live = self.filter_ping_results(ping_results)
        
        # If ping found some live IPs, use those as confirmed
        if ping_live:
            confirmed_ips = ping_live
        else:
            # If ping failed, try fallback methods
            confirmed_ips = []
            
            # Try TCP connect scan
            print("Ping failed, trying TCP connect scan...")
            tcp_results = self.tcp_connect_scan(ips)
            tcp_live = [ip for ip, alive in tcp_results.items() if alive]
            
            if tcp_live:
                confirmed_ips = tcp_live
            else:
                # Try ARP scan
                print("TCP scan failed, trying ARP scan...")
                arp_results = self.arp_scan(ips)
                arp_live = [ip for ip, alive in arp_results.items() if alive]
                confirmed_ips = arp_live
        
        # Build comprehensive results
        results = {}
        for ip in ips:
            ping_alive = ip in ping_live
            tcp_alive = ip in confirmed_ips
            
            # Try DNS lookup for additional info
            dns_results = self.dns_lookup([ip])
            has_dns = dns_results.get(ip, False)
            
            results[ip] = {
                'ip': ip,
                'ping_alive': ping_alive,
                'tcp_alive': tcp_alive,
                'confirmed_live': ip in confirmed_ips,
                'has_dns_record': has_dns,
                'detection_method': self._determine_detection_method(ip, ping_alive, tcp_alive)
            }
        
        return results
    
    def _determine_detection_method(self, ip: str, ping_alive: bool, tcp_alive: bool) -> str:
        """
        Determines which method successfully detected the IP.
        
        Args:
            ip (str): IP address
            ping_alive (bool): Whether ping detected it
            tcp_alive (bool): Whether TCP scan detected it
            
        Returns:
            str: Detection method used
        """
        if ping_alive:
            return 'ping'
        elif tcp_alive:
            return 'tcp_connect'
        else:
            return 'none'
    
    def get_live_ips_summary(self, detection_results: Dict[str, Dict]) -> str:
        """
        Returns a summary of live IP detection results.
        
        Args:
            detection_results (Dict[str, Dict]): Results from confirm_live_ips
            
        Returns:
            str: Formatted summary string
        """
        total_ips = len(detection_results)
        confirmed_live = len([r for r in detection_results.values() if r['confirmed_live']])
        ping_detected = len([r for r in detection_results.values() if r['ping_alive']])
        tcp_detected = len([r for r in detection_results.values() if r['tcp_alive']])
        dns_records = len([r for r in detection_results.values() if r['has_dns_record']])
        
        # Count detection methods
        methods = {}
        for result in detection_results.values():
            method = result['detection_method']
            methods[method] = methods.get(method, 0) + 1
        
        return (
            f"Live IP Detection Summary:\n"
            f"Total IPs: {total_ips}\n"
            f"Confirmed Live: {confirmed_live}\n"
            f"Ping Detected: {ping_detected}\n"
            f"TCP Detected: {tcp_detected}\n"
            f"DNS Records: {dns_records}\n"
            f"Detection Methods: {methods}"
        )
    
    def get_confirmed_live_ips(self, detection_results: Dict[str, Dict]) -> List[str]:
        """
        Extracts confirmed live IP addresses from detection results.
        
        Args:
            detection_results (Dict[str, Dict]): Results from confirm_live_ips
            
        Returns:
            List[str]: List of confirmed live IP addresses
        """
        return [ip for ip, result in detection_results.items() if result['confirmed_live']]


def main():
    """Test function for the live IP detector module."""
    detector = LiveIPDetector(timeout=3.0)
    
    # Test IPs
    test_ips = [
        "127.0.0.1",      # Localhost
        "8.8.8.8",        # Google DNS
        "1.1.1.1",        # Cloudflare DNS
        "192.168.1.1",    # Common router IP
        "10.0.0.1",       # Common private IP
        "172.16.0.1",     # Common private IP
        "192.168.100.1",  # Another private IP
    ]
    
    print("Testing Live IP Detector Module")
    print("=" * 50)
    
    # Simulate ping results
    ping_results = {}
    for ip in test_ips:
        ping_results[ip] = {
            'ip': ip,
            'alive': ip in ['127.0.0.1', '8.8.8.8', '1.1.1.1'],
            'response_time': 1.5 if ip in ['127.0.0.1', '8.8.8.8', '1.1.1.1'] else None,
            'return_code': 0 if ip in ['127.0.0.1', '8.8.8.8', '1.1.1.1'] else 1,
            'stdout': '',
            'stderr': '',
            'error': None
        }
    
    # Test detection
    print("Testing live IP detection...")
    results = detector.confirm_live_ips(ping_results)
    
    # Display results
    for ip, result in results.items():
        status = "✓ Live" if result['confirmed_live'] else "✗ Dead"
        method = f" ({result['detection_method']})" if result['detection_method'] != 'none' else ""
        dns = " [DNS]" if result['has_dns_record'] else ""
        print(f"{ip}: {status}{method}{dns}")
    
    # Get summary
    print(f"\n{detector.get_live_ips_summary(results)}")
    
    # Get confirmed live IPs
    live_ips = detector.get_confirmed_live_ips(results)
    print(f"\nConfirmed Live IPs: {live_ips}")


if __name__ == "__main__":
    main() 