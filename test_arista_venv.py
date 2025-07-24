#!/usr/bin/env python3
"""
test_arista_venv.py
-------------------
Standalone test script for Arista RIB parsing functionality using venv.
Tests the ability to retrieve and parse routing information from an Arista router and save results to files.
"""

from rib.arista import handle_routing_info
from rib.db_utils import rib_db_manage
from tabulate import tabulate

def test_arista_parsing():
    """
    Test the Arista parsing functionality by retrieving and displaying RIB data.
    Saves table output to a file for further inspection.
    """
    # Test parameters - update these with your actual device details
    router_name = "Arista-Router"
    router_ip = "10.0.12.2"
    username = "admin"
    password = "sshadmin123"
    print("🧪 Testing Arista RIB Parsing with venv")
    print("=" * 50)
    try:
        # Clear existing database
        rib_db_manage.clear()
        print("✅ Cleared existing RIB database")
        # Get routing info using the existing workflow
        result = handle_routing_info(router_name, router_ip, username, password)
        if result['success']:
            routes = result['routes']
            if routes:
                print(f"\n✅ Successfully parsed {len(routes)} routes")
                # Display results
                print("\n" + "="*80)
                print("ROUTING TABLE")
                print("="*80)
                print(tabulate(
                    routes,
                    headers="keys",
                    tablefmt="grid",
                    showindex=False
                ))
                # Check database
                db_entries = rib_db_manage.get_entries()
                print(f"\n📊 Database contains {len(db_entries)} entries")
                # Save to file
                with open("arista_routing_table_venv.txt", "w") as f:
                    f.write(tabulate(
                        routes,
                        headers="keys",
                        tablefmt="grid",
                        showindex=False
                    ))
                print("\n✅ Routing table saved to arista_routing_table_venv.txt")
            else:
                print("⚠️ No routes found - this might be normal if the device has no routes")
        else:
            print(f"❌ Failed to get routing info: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_arista_parsing() 