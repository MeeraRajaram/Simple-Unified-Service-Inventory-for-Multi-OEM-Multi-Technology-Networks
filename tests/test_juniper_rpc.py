"""
test_juniper_rpc.py
-------------------
Standalone test script for parsing Junos native RPC XML and displaying RIB entries in the required schema.
Usage: python test_juniper_rpc.py <juniper_rpc.xml>
"""

from rib.juniper_parse import parse_juniper_rpc_xml
from tabulate import tabulate

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python test_juniper_rpc.py <juniper_rpc.xml>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        xml_data = f.read()
    routes = parse_juniper_rpc_xml(xml_data, hostname="Juniper-Router")
    print(tabulate(routes, headers="keys", tablefmt="grid")) 