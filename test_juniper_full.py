#!/usr/bin/env python3
"""
Test script for full Juniper workflow: fetch XML, parse, and print table.
"""
from rib.juniper import handle_routing_info
from rib.juniper_parse import parse_juniper_rpc_xml
from tabulate import tabulate

def test_juniper_full():
    router_name = "10.0.13.2"  # Use the actual hostname or IP from your router info table
    router_ip = "10.0.13.2"
    username = "admin"
    password = "sshadmin123"
    print("🧪 Testing Full Juniper Workflow")
    print("=" * 50)
    result = handle_routing_info(router_name, router_ip, username, password)
    if result['success']:
        xml_str = result['rib_xml']
        routes = parse_juniper_rpc_xml(xml_str, router_name)
        if routes:
            print(f"\n✅ Successfully parsed {len(routes)} routes")
            print(tabulate(routes, headers="keys", tablefmt="grid"))
        else:
            print("⚠️ No routes found in XML data")
    else:
        print(f"❌ Failed to get routing info: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    test_juniper_full() 