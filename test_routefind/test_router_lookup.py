import unittest
from routefind.router_lookup import find_router_for_ip

class TestRouterLookup(unittest.TestCase):
    def test_cisco_lookup(self):
        result = find_router_for_ip('192.168.1.1')
        print('Cisco lookup result:', result)
        self.assertIsNotNone(result, 'Should find router for 192.168.1.1')
        self.assertEqual(result['vendor'].lower(), 'cisco')

    def test_juniper_lookup(self):
        result = find_router_for_ip('10.0.13.2')
        print('Juniper lookup result:', result)
        self.assertIsNotNone(result, 'Should find router for 10.0.13.2')
        self.assertEqual(result['vendor'].lower(), 'juniper')

    def test_arista_lookup(self):
        result = find_router_for_ip('10.0.12.2')
        print('Arista lookup result:', result)
        self.assertIsNotNone(result, 'Should find router for 10.0.12.2')
        self.assertEqual(result['vendor'].lower(), 'arista')

if __name__ == '__main__':
    unittest.main() 