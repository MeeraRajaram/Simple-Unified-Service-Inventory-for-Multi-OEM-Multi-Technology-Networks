"""
Template Manager for Configuration Push
Handles configuration templates for different network scenarios
"""

import json
import os
from typing import List, Dict, Optional
from dataclasses import dataclass
from configuration_push.vrf_manager import VRFManager
from configuration_push.device_manager import DeviceManager
import sqlite3

# Paths to your databases
ROUTERS_DB = 'routers.db'
INIP_DB = 'inip.db'
VRF_DB = 'vrf_db.sqlite3'

def get_loopbacks():
    """Fetch loopback IPs from inip.db as {router_name: loopback_ip}"""
    conn = sqlite3.connect(INIP_DB)
    cur = conn.cursor()
    loopbacks = {}
    try:
        cur.execute("SELECT router_name, ip FROM inip WHERE interface LIKE 'Loopback%'")
        for row in cur.fetchall():
            loopbacks[row[0]] = row[1]
    except Exception as e:
        print("Error fetching loopbacks:", e)
    conn.close()
    return loopbacks

def build_vrf_db():
    loopbacks = get_loopbacks()

    conn_r = sqlite3.connect(ROUTERS_DB)
    cur_r = conn_r.cursor()
    cur_r.execute("SELECT hostname, ip, vendor, software_version, username, password FROM routers")
    routers = cur_r.fetchall()
    conn_r.close()

    conn_vrf = sqlite3.connect(VRF_DB)
    cur_vrf = conn_vrf.cursor()
    cur_vrf.execute("""
        CREATE TABLE IF NOT EXISTS vrf_devices (
            router_name TEXT PRIMARY KEY,
            loopback_ip TEXT,
            mgmt_ip TEXT,
            vendor TEXT,
            software_version TEXT,
            username TEXT,
            password TEXT
        )
    """)

    for r in routers:
        name, mgmt_ip, vendor, sw, user, pw = r
        loopback = loopbacks.get(name, None)
        cur_vrf.execute("""
            INSERT OR REPLACE INTO vrf_devices
            (router_name, loopback_ip, mgmt_ip, vendor, software_version, username, password)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, loopback, mgmt_ip, vendor, sw, user, pw))

    conn_vrf.commit()
    conn_vrf.close()
    print("VRF DB built/updated successfully.")

if __name__ == '__main__':
    build_vrf_db()

@dataclass
class ConfigTemplate:
    id: str
    name: str
    description: str
    category: str
    vendor: str
    content: str
    variables: List[str]
    tags: List[str]

class TemplateManager:
    def __init__(self):
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> List[ConfigTemplate]:
        """Load default configuration templates"""
        return [
            ConfigTemplate(
                id="ospf_basic",
                name="OSPF Basic Configuration",
                description="Basic OSPF routing configuration for Cisco devices",
                category="routing",
                vendor="cisco",
                content="""router ospf 1
 network {network} {wildcard} area {area}
 passive-interface default
 no passive-interface {active_interface}
 router-id {router_id}""",
                variables=["network", "wildcard", "area", "active_interface", "router_id"],
                tags=["ospf", "routing", "cisco"]
            ),
            ConfigTemplate(
                id="bgp_basic",
                name="BGP Basic Configuration",
                description="Basic BGP routing configuration",
                category="routing",
                vendor="cisco",
                content="""router bgp {as_number}
 neighbor {neighbor_ip} remote-as {neighbor_as}
 network {network} mask {subnet_mask}
 neighbor {neighbor_ip} description {description}""",
                variables=["as_number", "neighbor_ip", "neighbor_as", "network", "subnet_mask", "description"],
                tags=["bgp", "routing", "cisco"]
            ),
            ConfigTemplate(
                id="vlan_config",
                name="VLAN Configuration",
                description="VLAN configuration for switches",
                category="switching",
                vendor="cisco",
                content="""vlan {vlan_id}
 name {vlan_name}
interface vlan {vlan_id}
 ip address {vlan_ip} {subnet_mask}
 no shutdown
interface {trunk_interface}
 switchport mode trunk
 switchport trunk allowed vlan {vlan_id}""",
                variables=["vlan_id", "vlan_name", "vlan_ip", "subnet_mask", "trunk_interface"],
                tags=["vlan", "switching", "cisco"]
            ),
            ConfigTemplate(
                id="acl_standard",
                name="Standard ACL Configuration",
                description="Standard Access Control List configuration",
                category="security",
                vendor="cisco",
                content="""access-list {acl_number} permit {source_network} {wildcard}
access-list {acl_number} deny any log
interface {interface}
 ip access-group {acl_number} {direction}""",
                variables=["acl_number", "source_network", "wildcard", "interface", "direction"],
                tags=["acl", "security", "cisco"]
            ),
            ConfigTemplate(
                id="interface_config",
                name="Interface Configuration",
                description="Basic interface configuration",
                category="interfaces",
                vendor="cisco",
                content="""interface {interface_name}
 description {description}
 ip address {ip_address} {subnet_mask}
 no shutdown""",
                variables=["interface_name", "description", "ip_address", "subnet_mask"],
                tags=["interface", "cisco"]
            ),
            ConfigTemplate(
                id="juniper_ospf",
                name="Juniper OSPF Configuration",
                description="OSPF configuration for Juniper devices",
                category="routing",
                vendor="juniper",
                content="""protocols {
    ospf {
        area {area} {
            interface {interface} {
                interface-type p2p;
            }
        }
    }
}""",
                variables=["area", "interface"],
                tags=["ospf", "routing", "juniper"]
            ),
            ConfigTemplate(
                id="arista_vlan",
                name="Arista VLAN Configuration",
                description="VLAN configuration for Arista switches",
                category="switching",
                vendor="arista",
                content="""vlan {vlan_id}
   name {vlan_name}
interface Vlan{vlan_id}
   ip address {vlan_ip}/{subnet_bits}
interface {trunk_interface}
   switchport mode trunk
   switchport trunk allowed vlan {vlan_id}""",
                variables=["vlan_id", "vlan_name", "vlan_ip", "subnet_bits", "trunk_interface"],
                tags=["vlan", "switching", "arista"]
            )
        ]
    
    def get_all_templates(self) -> List[Dict]:
        """Get all available templates"""
        return [self._template_to_dict(template) for template in self.templates]
    
    def get_template_by_id(self, template_id: str) -> Optional[ConfigTemplate]:
        """Get a specific template by ID"""
        for template in self.templates:
            if template.id == template_id:
                return template
        return None
    
    def get_templates_by_category(self, category: str) -> List[ConfigTemplate]:
        """Get templates filtered by category"""
        return [t for t in self.templates if t.category.lower() == category.lower()]
    
    def get_templates_by_vendor(self, vendor: str) -> List[ConfigTemplate]:
        """Get templates filtered by vendor"""
        return [t for t in self.templates if t.vendor.lower() == vendor.lower()]
    
    def get_templates_by_tag(self, tag: str) -> List[ConfigTemplate]:
        """Get templates filtered by tag"""
        return [t for t in self.templates if tag.lower() in [t.lower() for t in t.tags]]
    
    def render_template(self, template_id: str, variables: Dict[str, str]) -> str:
        """
        Render a template with provided variables
        
        Args:
            template_id: ID of the template to render
            variables: Dictionary of variable names and values
            
        Returns:
            Rendered configuration content
        """
        template = self.get_template_by_id(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Check if all required variables are provided
        missing_vars = [var for var in template.variables if var not in variables]
        if missing_vars:
            raise ValueError(f"Missing required variables: {', '.join(missing_vars)}")
        
        # Render the template
        try:
            return template.content.format(**variables)
        except KeyError as e:
            raise ValueError(f"Invalid variable in template: {e}")
    
    def add_template(self, template: ConfigTemplate):
        """Add a new template"""
        # Check if template ID already exists
        if self.get_template_by_id(template.id):
            raise ValueError(f"Template with ID {template.id} already exists")
        
        self.templates.append(template)
    
    def update_template(self, template_id: str, updated_template: ConfigTemplate):
        """Update an existing template"""
        for i, template in enumerate(self.templates):
            if template.id == template_id:
                self.templates[i] = updated_template
                return
        
        raise ValueError(f"Template {template_id} not found")
    
    def delete_template(self, template_id: str):
        """Delete a template"""
        self.templates = [t for t in self.templates if t.id != template_id]
    
    def get_categories(self) -> List[str]:
        """Get all available template categories"""
        return list(set(template.category for template in self.templates))
    
    def get_vendors(self) -> List[str]:
        """Get all available template vendors"""
        return list(set(template.vendor for template in self.templates))
    
    def get_tags(self) -> List[str]:
        """Get all available template tags"""
        all_tags = []
        for template in self.templates:
            all_tags.extend(template.tags)
        return list(set(all_tags))
    
    def _template_to_dict(self, template: ConfigTemplate) -> Dict:
        """Convert ConfigTemplate to dictionary for JSON serialization"""
        return {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'category': template.category,
            'vendor': template.vendor,
            'variables': template.variables,
            'tags': template.tags
        }
    
    def search_templates(self, query: str) -> List[ConfigTemplate]:
        """Search templates by name, description, or tags"""
        query = query.lower()
        results = []
        
        for template in self.templates:
            if (query in template.name.lower() or 
                query in template.description.lower() or
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)
        
        return results 