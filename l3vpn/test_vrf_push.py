from vrf import WebVRFManager

if __name__ == "__main__":
    # Test credentials and device
    host = "192.168.0.2"
    port = 830
    username = "admin"
    password = "sshadmin123"

    # Sample VRF config
    vrf_name = "TEST_VRF"
    rd = "6500:800"
    route_targets = ["import,6500:800", "export,6500:800"]
    description = "Test VRF from script"

    mgr = WebVRFManager(host, port, username, password)
    try:
        if mgr.connect():
            print(f"\n🔄 Pushing VRF config to {host}...")
            result = mgr.create_vrf(vrf_name, rd, route_targets, description)
            print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        mgr.close() 