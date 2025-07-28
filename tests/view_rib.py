"""
view_rib.py
-----------
Standalone script to test Arista RIB XML retrieval and parsing using handle_routing_info.
Prints the raw XML and parsed route table for a given Arista device.
"""

from rib.arista import handle_routing_info

# Run the test case to populate the RIB table and get XML and parsed routes for Arista
result = handle_routing_info("Arista1", "10.0.12.2", "admin", "sshadmin123")

if result.get('success'):
    print("\n--- Arista RIB XML ---\n")
    print(result['rib_xml'])
    print("\n--- Parsed Arista RIB Table ---\n")
    routes = result['routes']
    if routes:
        # Print as a table
        headers = ["Router", "Loopback IP", "Protocol", "Destination", "Interface", "Next Hop"]
        print("\t".join(headers))
        print("-" * 80)
        for route in routes:
            print("\t".join([route.get(h, '') for h in headers]))
    else:
        print("No routes parsed.")
else:
    print(f"Error: {result.get('error')}") 