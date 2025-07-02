import re
from ncclient import manager
from ncclient.xml_ import new_ele, sub_ele
import xml.etree.ElementTree as ET
from tabulate import tabulate

def get_namespace(element):
    m = re.match(r'\{.*\}', element.tag)
    return m.group(0) if m else ''

def get_interface_info(mgr):
    """Get interface information in terse format"""
    rpc = new_ele("get-interface-information")
    sub_ele(rpc, "terse")
    response = mgr.dispatch(rpc)
    return ET.fromstring(str(response))

def format_interface_output(root):
    """Format interface output as a table matching 'show interfaces terse'"""
    table_data = []
    headers = ["Interface", "Admin", "Link", "Proto", "Local", "Remote"]
    ns = get_namespace(root)
    
    # Process all interfaces (physical and logical)
    for phy in root.findall(f".//{ns}physical-interface"):
        if_name = phy.findtext(f"{ns}name", "").strip()
        admin = phy.findtext(f"{ns}admin-status", "down").lower()
        link = phy.findtext(f"{ns}oper-status", "down").lower()
        
        # Physical interface row
        table_data.append([if_name, admin, link, "", "", ""])
        
        # Logical interfaces
        for logi in phy.findall(f"{ns}logical-interface"):
            unit = logi.findtext(f"{ns}name", "").replace(if_name, "").strip(".")
            l_admin = logi.findtext(f"{ns}admin-status", "down").lower()
            l_link = logi.findtext(f"{ns}oper-status", "down").lower()
            
            # Get all address families
            addr_families = []
            for fam in logi.findall(f"{ns}address-family"):
                proto = fam.findtext(f"{ns}address-family-name", "").strip()
                for addr in fam.findall(f"{ns}interface-address/{ns}ifa-local"):
                    ip = addr.text.strip() if addr.text else ""
                    addr_families.append((proto, ip))
            
            if addr_families:
                for i, (proto, ip) in enumerate(addr_families):
                    if i == 0:
                        table_data.append([f"{if_name}.{unit}", l_admin, l_link, proto, ip, ""])
                    else:
                        table_data.append(["", "", "", proto, ip, ""])
            else:
                table_data.append([f"{if_name}.{unit}", l_admin, l_link, "", "", ""])
    
    return tabulate(table_data, headers=headers, tablefmt="grid")

def get_physical_inventory(m):
    interfaces_xml = format_interface_output(get_interface_info(m))
    return interfaces_xml