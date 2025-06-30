#!/usr/bin/env python3
"""
Test script for enhanced Arista RIB parsing functionality
"""

from rib.arista_parse import parse_rib_xml_enhanced
from rib.db_utils import rib_db_manage
from tabulate import tabulate

def test_arista_parsing():
    """Test the enhanced Arista parsing functionality"""
    
    # Test parameters - update these with your actual device details
    router_name = "Arista-Router"
    router_ip = "10.0.12.2"
    username = "admin"
    password = "sshadmin123"
    
    print("🧪 Testing Enhanced Arista RIB Parsing")
    print("=" * 50)
    
    try:
        # Clear existing database
        rib_db_manage.clear()
        print("✅ Cleared existing RIB database")
        
        # Parse RIB data
        routes = parse_rib_xml_enhanced(router_name, router_ip, username, password)
        
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
            with open("arista_routing_table.txt", "w") as f:
                f.write(tabulate(
                    routes,
                    headers="keys",
                    tablefmt="grid",
                    showindex=False
                ))
            print("\n✅ Routing table saved to arista_routing_table.txt")
            
        else:
            print("⚠️ No routes found - this might be normal if the device has no routes")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_arista_parsing() 