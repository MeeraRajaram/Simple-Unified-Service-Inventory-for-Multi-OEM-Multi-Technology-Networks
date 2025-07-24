#!/usr/bin/env python3
"""
IP Pinger Module

This module pings IP addresses to determine which ones are responsive.
It uses ICMP ping and provides fallback methods for different scenarios.

Author: IP Scanner Automation System
"""

import subprocess
import socket
import threading
import time
from typing import List, Dict, Optional
import platform
import queue


class IPPinger:
    """Pings IP addresses to determine responsiveness."""
    
    def __init__(self, timeout: float = 1.0, max_threads: int = 50):
        """
        Initialize the IP pinger.
        
        Args:
            timeout (float): Timeout for each ping in seconds
            max_threads (int): Maximum number of concurrent ping threads
        """
        self.timeout = timeout
        self.max_threads = max_threads
        self.results = {}
        self.ping_queue = queue.Queue()
        self.result_queue = queue.Queue()
    
    def ping_ip(self, ip: str) -> Dict:
        """
        Pings a single IP address.
        
        Args:
            ip (str): IP address to ping
            
        Returns:
            Dict: Ping results with status and details
        """
        try:
            # Determine OS and use appropriate ping command
            if platform.system().lower() == "windows":
                cmd = ["ping", "-n", "1", "-w", str(int(self.timeout * 1000)), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(self.timeout)), ip]
            
            # Execute ping command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 1
            )
            
            # Parse results
            is_alive = result.returncode == 0
            
            # Extract response time if available
            response_time = None
            if is_alive:
                # Try to extract response time from output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'time=' in line or 'time<' in line:
                        # Extract time value
                        time_part = line.split('time=')[-1].split()[0] if 'time=' in line else line.split('time<')[0]
                        try:
                            response_time = float(time_part.replace('ms', ''))
                        except ValueError:
                            response_time = None
                        break
            
            return {
                'ip': ip,
                'alive': is_alive,
                'response_time': response_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'error': None
            }
            
        except subprocess.TimeoutExpired:
            return {
                'ip': ip,
                'alive': False,
                'response_time': None,
                'return_code': -1,
                'stdout': '',
                'stderr': '',
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'ip': ip,
                'alive': False,
                'response_time': None,
                'return_code': -1,
                'stdout': '',
                'stderr': '',
                'error': str(e)
            }
    
    def _ping_worker(self):
        """Worker thread for pinging IPs from the queue."""
        while True:
            try:
                ip = self.ping_queue.get_nowait()
                result = self.ping_ip(ip)
                self.result_queue.put(result)
                self.ping_queue.task_done()
            except queue.Empty:
                break
    
    def ping_multiple_ips(self, ips: List[str]) -> Dict[str, Dict]:
        """
        Pings multiple IP addresses concurrently.
        
        Args:
            ips (List[str]): List of IP addresses to ping
            
        Returns:
            Dict[str, Dict]: Dictionary mapping IP to ping results
        """
        results = {}
        
        # Add IPs to queue
        for ip in ips:
            self.ping_queue.put(ip)
        
        # Start worker threads
        threads = []
        num_threads = min(self.max_threads, len(ips))
        
        for _ in range(num_threads):
            thread = threading.Thread(target=self._ping_worker)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Collect results
        while not self.result_queue.empty():
            result = self.result_queue.get()
            results[result['ip']] = result
        
        return results
    
    def ping_subnet(self, subnet_ips: List[str]) -> Dict[str, Dict]:
        """
        Pings all IPs in a subnet and returns results.
        
        Args:
            subnet_ips (List[str]): List of IP addresses from subnet parser
            
        Returns:
            Dict[str, Dict]: Dictionary mapping IP to ping results
        """
        print(f"Pinging {len(subnet_ips)} IP addresses...")
        return self.ping_multiple_ips(subnet_ips)
    
    def get_live_ips(self, ping_results: Dict[str, Dict]) -> List[str]:
        """
        Extracts live IP addresses from ping results.
        
        Args:
            ping_results (Dict[str, Dict]): Results from ping operations
            
        Returns:
            List[str]: List of live IP addresses
        """
        live_ips = []
        for ip, result in ping_results.items():
            if result['alive']:
                live_ips.append(ip)
        return live_ips
    
    def get_ping_summary(self, ping_results: Dict[str, Dict]) -> str:
        """
        Returns a summary of ping results.
        
        Args:
            ping_results (Dict[str, Dict]): Results from ping operations
            
        Returns:
            str: Formatted summary string
        """
        total_ips = len(ping_results)
        live_ips = len([r for r in ping_results.values() if r['alive']])
        dead_ips = total_ips - live_ips
        
        # Calculate average response time for live IPs
        response_times = [r['response_time'] for r in ping_results.values() 
                         if r['alive'] and r['response_time'] is not None]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return (
            f"Ping Summary:\n"
            f"Total IPs: {total_ips}\n"
            f"Live IPs: {live_ips}\n"
            f"Dead IPs: {dead_ips}\n"
            f"Success Rate: {(live_ips/total_ips)*100:.1f}%\n"
            f"Average Response Time: {avg_response_time:.2f}ms"
        )
    
    def quick_scan(self, ips: List[str], sample_size: int = 10) -> bool:
        """
        Performs a quick scan of a sample of IPs to determine if subnet is active.
        
        Args:
            ips (List[str]): List of IP addresses
            sample_size (int): Number of IPs to sample
            
        Returns:
            bool: True if at least one IP in sample is alive
        """
        if len(ips) <= sample_size:
            sample_ips = ips
        else:
            # Take evenly distributed sample
            step = len(ips) // sample_size
            sample_ips = [ips[i] for i in range(0, len(ips), step)][:sample_size]
        
        print(f"Quick scan: testing {len(sample_ips)} IPs out of {len(ips)}")
        results = self.ping_multiple_ips(sample_ips)
        
        live_count = len([r for r in results.values() if r['alive']])
        print(f"Quick scan found {live_count} live IPs in sample")
        
        return live_count > 0


def main():
    """Test function for the IP pinger module."""
    pinger = IPPinger(timeout=2.0)
    
    # Test IPs (mix of common local and public IPs)
    test_ips = [
        "127.0.0.1",      # Localhost
        "8.8.8.8",        # Google DNS
        "1.1.1.1",        # Cloudflare DNS
        "192.168.1.1",    # Common router IP
        "10.0.0.1",       # Common private IP
        "172.16.0.1",     # Common private IP
        "192.168.100.1",  # Another private IP
    ]
    
    print("Testing IP Pinger Module")
    print("=" * 50)
    
    # Test individual ping
    print("\nTesting individual ping:")
    result = pinger.ping_ip("127.0.0.1")
    print(f"127.0.0.1: {'✓ Alive' if result['alive'] else '✗ Dead'}")
    if result['response_time']:
        print(f"Response time: {result['response_time']}ms")
    
    # Test multiple IPs
    print("\nTesting multiple IPs:")
    results = pinger.ping_multiple_ips(test_ips)
    
    for ip, result in results.items():
        status = "✓ Alive" if result['alive'] else "✗ Dead"
        response = f" ({result['response_time']:.1f}ms)" if result['response_time'] else ""
        print(f"{ip}: {status}{response}")
    
    # Get summary
    print(f"\n{pinger.get_ping_summary(results)}")
    
    # Get live IPs
    live_ips = pinger.get_live_ips(results)
    print(f"\nLive IPs: {live_ips}")


if __name__ == "__main__":
    main() 