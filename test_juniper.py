#!/usr/bin/env python3
"""
Test script for Juniper RIB parsing functionality
"""
from rib.juniper import handle_routing_info
from rib.db_utils import rib_db_manage
from tabulate import tabulate

def test_juniper_parsing():
    """Test the Juniper parsing functionality"""
    router_name = "Juniper-Router"
    router_ip = "10.0.13.2"
    username = "admin"
    password = "sshadmin123"
    print("🧪 Testing Juniper RIB Parsing")
    print("=" * 50)
    try:
        # Clear existing database
        rib_db_manage.clear()
        print("✅ Cleared existing RIB database")
        # Get routing info using the handler
        result = handle_routing_info(router_name, router_ip, username, password)
        if result['success']:
            routes = result['routes']
            if routes:
                print(f"\n✅ Successfully parsed {len(routes)} routes")
                print("\n--- XML ---\n")
                print(result['rib_xml'])
                print("\n--- TABLE ---\n")
                print(tabulate(
                    routes,
                    headers="keys",
                    tablefmt="grid",
                    showindex=False
                ))
                # Save XML to file
                with open("juniper_routing.xml", "w") as f:
                    f.write(result['rib_xml'])
                # Save table to file
                with open("juniper_routing_table.txt", "w") as f:
                    f.write(tabulate(
                        routes,
                        headers="keys",
                        tablefmt="grid",
                        showindex=False
                    ))
                print("\n✅ Routing table saved to juniper_routing_table.txt")
            else:
                print("⚠️ No routes found - this might be normal if the device has no routes")
        else:
            print(f"❌ Failed to get routing info: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_juniper_parsing() 