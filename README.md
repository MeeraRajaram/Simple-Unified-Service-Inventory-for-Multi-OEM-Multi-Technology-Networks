# GNS3 WebApp: English-Driven Network Automation and Visualization

## Abstract

This project presents a novel, web-based network automation and visualization platform designed for non-technical users. Built atop Flask, SQLite, and NETCONF/YANG, the app enables users to discover, visualize, and configure complex network topologies using only English-driven workflows—no CLI or protocol expertise required. The system automates network discovery, topology and protocol visualization, RIB parsing, pathfinding, and L3VPN/VRF configuration push, with a focus on usability, modularity, and IEEE-grade code quality.

---

## Features

- **English-Only User Experience**: All workflows are accessible via intuitive web forms and tables—no CLI, no config syntax, no protocol knowledge required.
- **Automated Network Discovery**: Ping sweep, port scan, and NETCONF-based device/vendor detection.
- **Live Topology Visualization**: Interactive, protocol-aware network maps and pathfinding.
- **RIB Parsing and Display**: Multi-vendor RIB extraction and visualization.
- **Configuration Push**: L3VPN/VRF service creation and interface assignment via NETCONF/YANG.
- **Database-Driven**: All state (discovery, RIB, VRF, push data) is stored in SQLite for auditability and reproducibility.
- **IEEE-Ready Codebase**: All modules and scripts are documented with professional docstrings and modular design.
- **Testing Suite**: Includes pytest/unittest-based tests for critical modules and workflows.

---

## Project Structure
gns3-webapp/
│
├── app.py                      # Main backend entry point (Flask/Django/FastAPI)
├── OUTPUTS                     #Folder containing screenshots of outputs for reference 
├── OUTPUT_DEMO                 #Folder containing output as screen recording , after execution of website on localhost 
│
├── templates/                  # All HTML (Jinja2) templates for frontend
│   ├── index.html
│   ├── alive_ips.html
│   ├── base.html
│   ├── configuration_push.html
│   ├── inventory.html
│   ├── routers.html
│   ├── rib/
│   │   ├── rib.html
│   │   └── rib_history.html
|   |── routefind/
|   |   ├── find_rotuer.html
│   │   └── index.html
|   |   ├── route_pair_result.html
│   │   └── route_result.html
│   ├── topology/
│   │   ├── topology_view.html
|   |   ├── protocol_topology_view.html
│   │   └── topology_visualization.html
│   ├── pathfinder/
│   │   └── pathfinder.html
│   ├── configuration_push.html
|   |   └── index.html
│   └── l3vpn/
│   |   └── vpn_services.html
|   └── services_physical/
│   |   └── services_physical.html
│
├── static/css/                     # Static files (CSS, JS, images)
│   ├── #style.css
│  
│
├── blueprints/                 # Flask blueprints (modular routes/views)
│   ├── inventory.py
│   ├── rib.py
│   ├── topology/
│   │   ├── __init__.py
│   │   └── topology.py
│   │   └── protocol_utils.py
│   ├── main.py
│   ├── pathfinder.py
│   ├── scan.py
│   ├── services_physical.py
│   ├── view.py
│   └── configuration_push.py
│
├── services/                   # Backend service modules (network logic, DB, NETCONF, SSH)
│   ├── __init__.py
│   ├── db.py                   # Router DB logic (add, clear, get routers, etc.)
│   ├── vendor_host.py          # NETCONF/SNMP device info fetch
│   ├── netconf_service.py      # NETCONF interface/protocol scan
│   ├── ports_protocols.py      # Interface/protocol parsing
│   ├── rib.py                  # RIB DB logic
│   ├── gns3_service.py                
│   ├── rib.py                 
│   ├── vendor_detect.py                 
│   ├── scan_service.py         # Ping sweep, live IP detection
│   └── inventory_service.py    # IP/CIDR validation
│
├── services_physical/                 # Flask blueprints (modular routes/views)
│   ├── arista_phy.py
│   ├── arista_serv.py
│   ├── cisco_phy.py
│   ├── cisco_serv.py
│   ├── juniper_phy.py
│   ├── juniper_serv.py
│   ├── forms.py
│   ├── models.py
│   ├── utils.py
│   ├── views.py
│   ├── juniper_serv_test.py
│   ├── juniper_phy_test.py
│   └── main.py
│
├── configuration_push/                        # RIB parsing and vendor-specific logic
│   ├── __init__.py
│   ├── bgp_check.py
│   ├── interface_manager.py
│   ├── loopback_fetcher.py
│   ├── README.md
│   └── template_manager.py
│
├── pathfinder/               
│   ├── __init__.py
│   ├── allpaths.db
│   ├── primary_path.db
│   ├── altpaths.db
│   ├── data.py
│   ├── find.py
│   ├── path.db
│   ├── path.py
│   └── valid.py
│
│
├── rib/                        # RIB parsing and vendor-specific logic
│   ├── db_parser.py
│   ├── db_utils.py
│   ├── cisco.py
│   ├── arista.py
│   ├── juniper.py
│   ├── nokia.py
│   ├── cisco_parse.py
│   ├── arista_parse.py
│   ├── juniper_parse.py
│   ├── nokia_parse.py
│   ├── huawei.py
│   └── huawei_parse.py
│
├── l3vpn/                      # L3VPN/VRF logic and workflow
│   ├── vrf.py                  # VRF push logic (WebVRFManager, etc.)
│   ├── main.py                
│   ├── netconf.py                 
│   ├── vrf_db_manager.py       # VRF DB logic (populate, update, fetch)
│   └── test_vrf_push.py        # Standalone VRF push test script
│
├── routefind/                  # Pathfinding and router lookup logic
│   ├── __init__.py
│   ├── templates/
│   │   ├── index.html
│   │   └── lookup_result.html
│   ├── router_finder.py
│   ├── router_lookup.py
│   ├── routes.py
│   ├── path_finder.py
│   ├── metwork_visualization.py
│   └── ip_validator.py
│
├── test_routefind/                  # Pathfinding and router lookup logic
│   ├── test_ip_validator.py
│   └── test_router_lookup.py
├── topo/                       # Topology learning and INIP/directconn logic
│   ├── __init__.py
│   ├── topo_inip.py
│   ├── test_connections.py
│   ├── topo_connections.py
│   └── test_inip.py
│
├── routers.db                  # SQLite DB for discovered routers
├── rib_db.sqlite3              # SQLite DB for RIB entries
├── inip.db                     # SQLite DB for interface IPs
├── directconndb                # SQLite DB for direct connections
├── vrf.db                      # SQLite DB for VRF config
├── arista_routing_table_venv.txt                
├── ospfdb                   
├── proto_routes.db                    
├── protodb                  
├── push_data                 
├── push_data.db                    
├── requirements.txt                
├── SELECT                     
├── service_discovery_log       
├── test_arista_enhanced.py          
├── test_arista_venv.py           
├── test_device_info.py                      
├── test_juniper_full.py                     
├── test_juniper_rpc.py                     
├── test_juniper.py                     
├── test_router_finder_mock.py                    
├── test_router_finder.py                    
├── view_rib.py                     
├── vrf_db.sqlite3                         
│
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation

## Setup & Installation

1. **Clone the repository**  
   ```bash
   git clone <your-repo-url>
   cd webapp
   ```

2. **Create and activate a virtual environment (recommended)**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the app**  
   ```bash
   python3 app.py
   ```
   The app will automatically find a free port (default: 5006).

5. **Access the web UI**  
   Open your browser to:  
   ```
   http://localhost:5006/
   ```

---

## Usage Guide

### Web UI Workflows

- **Inventory Discovery**:  
  Enter an IP and subnet, scan for live devices, and provide credentials. The app auto-detects vendors and populates the inventory.

- **Topology Visualization**:  
  View live network topology, protocol overlays, and pathfinding results. All visualizations are interactive and require no CLI.

- **RIB Table & Pathfinding**:  
  Inspect routing tables and find optimal paths between routers using the web interface.

- **Configuration Push (L3VPN/VRF)**:  
  - Select a path and populate the push data table.
  - Enter VRF details and assign interfaces via the UI.
  - Push VRF configs to all routers in the path with a single click.
  - View results and debug output in the UI.

### CLI & Testing

- **Run unit tests**  
  ```bash
  pytest test_routefind/
  ```
  or
  ```bash
  python3 -m unittest discover test_routefind/
  ```

- **Standalone scripts**  
  - `test_device_info.py`: Test NETCONF device info retrieval.
  - `test_router_finder.py`: Debug router lookup logic.
  - `test_juniper.py`, `test_arista_venv.py`: Vendor-specific RIB parsing tests.

---

## Novelty & Academic Value

- **English-Only Automation**:  
  Designed for users with no network protocol or CLI knowledge.
- **Live, Multi-Vendor Support**:  
  Works with Cisco, Juniper, Arista, and is easily extensible.
- **Self-Contained, Reproducible**:  
  No external dependencies or sys.path hacks; all logic is in-repo and database-driven.
- **IEEE-Ready Documentation**:  
  All code is documented with professional, PEP-257/IEEE-style docstrings.

---

## Contribution & Citation

- **Contributions**:  
  Please submit pull requests with clear docstrings and tests.
- **Citation**:  
  If using this project in academic work, please cite as:  
  ```
  <Your Name>, "English-Driven Web-Based Network Automation and Visualization," IEEE, 2024.
  ```

---

## Contact

For questions, issues, or collaboration, please contact:  
<your-email@example.com>

---

**For more details, see comments and docstrings in each module.** 
