from ncclient import manager

def detect_vendor_via_netconf(ip, username='admin', password='admin', port=830):
    try:
        with manager.connect(
            host=ip,
            port=port,
            username=username,
            password=password,
            hostkey_verify=False,
            allow_agent=False,
            look_for_keys=False,
            timeout=5
        ) as m:
            caps = "\n".join(m.server_capabilities)
            if 'cisco' in caps.lower():
                return 'Cisco'
            elif 'arista' in caps.lower():
                return 'Arista'
            elif 'juniper' in caps.lower():
                return 'Juniper'
            elif 'huawei' in caps.lower():
                return 'Huawei'
            elif 'nokia' in caps.lower():
                return 'Nokia'
            else:
                return 'Unknown'
    except Exception as e:
        print(f"NETCONF vendor detection failed for {ip}: {e}")
        return 'Unknown' 