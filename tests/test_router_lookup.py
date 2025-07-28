"""
test_routefind/test_router_lookup.py
-----------------------------------
Unit tests for routefind.router_lookup.find_router_for_ip function.
Tests router lookup for Cisco, Juniper, and Arista devices by IP address.
"""

import unittest
from routefind.router_lookup import find_router_for_ip

class TestRouterLookup(unittest.TestCase):
    """
    Unit tests for router lookup by IP address and vendor detection.
    """
    def test_cisco_lookup(self):
        """
        Test that a Cisco router is found and vendor is correctly detected for 192.168.1.1.
        """
        result = find_router_for_ip('192.168.1.1')
        print('Cisco lookup result:', result)
        self.assertIsNotNone(result, 'Should find router for 192.168.1.1')
        self.assertEqual(result['vendor'].lower(), 'cisco')

    def test_juniper_lookup(self):
        """
        Test that a Juniper router is found and vendor is correctly detected for 10.0.13.2.
        """
        result = find_router_for_ip('10.0.13.2')
        print('Juniper lookup result:', result)
        self.assertIsNotNone(result, 'Should find router for 10.0.13.2')
        self.assertEqual(result['vendor'].lower(), 'juniper')

    def test_arista_lookup(self):
        """
        Test that an Arista router is found and vendor is correctly detected for 10.0.12.2.
        """
        result = find_router_for_ip('10.0.12.2')
        print('Arista lookup result:', result)
        self.assertIsNotNone(result, 'Should find router for 10.0.12.2')
        self.assertEqual(result['vendor'].lower(), 'arista')

if __name__ == '__main__':
    unittest.main() 