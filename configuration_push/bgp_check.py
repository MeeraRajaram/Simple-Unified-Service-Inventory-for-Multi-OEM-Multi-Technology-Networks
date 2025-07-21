from ncclient import manager
import socket

def check_bgp_support(device, timeout=5):
    """
    device: dict with keys host, port, username, password
    Returns True if BGP YANG model is supported, else False
    """
    try:
        with manager.connect(
            host=device['host'],
            port=device.get('port', 830),
            username=device['username'],
            password=device['password'],
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=timeout
        ) as m:
            capabilities = list(m.server_capabilities)
            for cap in capabilities:
                if "Cisco-IOS-XE-bgp" in cap or "openconfig-bgp" in cap or "bgp" in cap.lower():
                    return True
            return False
    except Exception as e:
        return False

def check_bgp_support_for_routers(router_loopbacks, username, password, port=830, timeout=5):
    """
    router_loopbacks: dict {router_name: loopback_ip}
    Returns: dict {router_name: True/False}
    """
    results = {}
    for router, loopback in router_loopbacks.items():
        if not loopback:
            results[router] = False
            continue
        device = {
            'host': loopback,
            'port': port,
            'username': username,
            'password': password
        }
        results[router] = check_bgp_support(device, timeout=timeout)
    return results 