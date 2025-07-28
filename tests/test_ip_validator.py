import unittest
from routefind.ip_validator import is_valid_ip, validate_ip_with_subnet

class TestIPValidator(unittest.TestCase):
    def test_is_valid_ip(self):
        valid_ips = [
            '192.168.1.1',
            '10.0.0.1',
            '255.255.255.255',
            '0.0.0.0',
            '2001:0db8:85a3:0000:0000:8a2e:0370:7334',  # IPv6
            '::1',  # IPv6 loopback
        ]
        invalid_ips = [
            '256.256.256.256',
            '192.168.1.256',
            'abc.def.ghi.jkl',
            '1234:5678:9abc:defg::1',  # Invalid IPv6
            '',
            None,
        ]
        for ip in valid_ips:
            with self.subTest(ip=ip):
                self.assertTrue(is_valid_ip(ip), f"Should be valid: {ip}")
        for ip in invalid_ips:
            with self.subTest(ip=ip):
                self.assertFalse(is_valid_ip(ip), f"Should be invalid: {ip}")

    def test_validate_ip_with_subnet(self):
        # Valid cases
        self.assertEqual(validate_ip_with_subnet('192.168.1.10', '192.168.1.0/24'), (True, 'Valid IP for the given subnet'))
        self.assertEqual(validate_ip_with_subnet('10.0.0.5', '10.0.0.0/8'), (True, 'Valid IP for the given subnet'))
        # Network address
        self.assertEqual(validate_ip_with_subnet('192.168.1.0', '192.168.1.0/24'), (False, 'IP cannot be network address or broadcast address'))
        # Broadcast address
        self.assertEqual(validate_ip_with_subnet('192.168.1.255', '192.168.1.0/24'), (False, 'IP cannot be network address or broadcast address'))
        # Outside subnet
        self.assertEqual(validate_ip_with_subnet('192.168.2.1', '192.168.1.0/24'), (False, 'IP is not within the subnet range'))
        # Invalid IP
        valid, msg = validate_ip_with_subnet('999.999.999.999', '192.168.1.0/24')
        self.assertFalse(valid)
        self.assertIn('Invalid IP or subnet format', msg)
        # Invalid subnet
        valid, msg = validate_ip_with_subnet('192.168.1.10', '192.168.1.0/33')
        self.assertFalse(valid)
        self.assertIn('Invalid IP or subnet format', msg)

if __name__ == '__main__':
    unittest.main() 