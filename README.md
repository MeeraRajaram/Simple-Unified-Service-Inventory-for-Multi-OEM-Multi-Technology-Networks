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

```
webapp/
│
├── app.py                  # Main Flask app entry point
├── requirements.txt        # Python dependencies
│
├── blueprints/             # Flask blueprints (UI routes, API endpoints)
│   ├── main.py
│   ├── inventory.py
│   ├── configuration_push.py
│   ├── topology/
│   │   ├── topology.py
│   │   ├── protocol_utils.py
│   └── ...
│
├── services/               # Backend services (DB, NETCONF, protocol helpers)
│   ├── db.py
│   ├── netconf_service.py
│   ├── ports_protocols.py
│   ├── vendor_host.py
│   └── ...
│
├── l3vpn/                  # L3VPN/VRF push logic
│   ├── vrf.py
│   ├── vrf_db_manager.py
│   ├── main.py
│   └── ...
│
├── rib/                    # RIB parsing and vendor-specific logic
│   ├── arista.py
│   ├── cisco_parse.py
│   └── ...
│
├── routefind/              # Pathfinding, IP validation, visualization
│   ├── ip_validator.py
│   ├── network_visualizer.py
│   └── ...
│
├── templates/              # Jinja2 HTML templates (UI)
│   └── ...
│
├── static/                 # Static assets (CSS, JS)
│   └── ...
│
├── test_routefind/         # Unit and integration tests
│   └── ...
│
├── <various .db files>     # SQLite databases (routers, RIB, VRF, etc.)
└── README.md               # This file
```

---

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

### Webapp Platform Notes
- **This webapp is Linux-based** and is designed to run on a Linux host.
- **tap0 interface is required**: The host must have a `tap0` interface configured and connected to the GNS3 topology's Cloud node for management and ping reachability.
- **Router loopbacks must be assigned** for proper discovery and pathfinding.

### GNS3 Lab Setup & Usage

#### 🖼️ Supported Topologies

**Topology 1: Cisco–Arista–Juniper Triangle**
- Cisco Catalyst 8000v
- Juniper vSRX
- Arista vEOS

**Topology 2: Full-Mesh 4-Router Cisco Lab**
- 4 Cisco Routers in full-mesh
- OSPF-enabled for pathfinding

#### 🧰 Prerequisites
- GNS3 installed
- Licensed appliances: CSR1000v, C8000v, Juniper vSRX, Arista vEOS
- `tap0` configured in GNS3 to bridge host and topology
- Host must be able to ping router IPs (e.g., 192.168.100.2)

#### 🖧 Topology 1 Setup
| Device      | Interface | IP            | Connected To |
|-------------|-----------|---------------|--------------|
| Cisco8000v  | Gi1       | 10.0.12.1/24  | Arista       |
|             | Gi2       | 10.0.13.1/24  | Juniper      |
|             | Gi3       | 192.168.100.2 | tap0         |
| Arista      | Eth1      | 10.0.12.2/24  | Cisco        |
|             | Eth2      | 10.0.14.1/24  | Juniper      |
| Juniper     | ge-0/0/0  | 10.0.13.2/24  | Cisco        |
|             | ge-0/0/1  | 10.0.14.2/24  | Arista       |

**OSPF Sample Configs:**

- **Cisco**
  ```
  conf t
  router ospf 1
   network 10.0.12.0 0.0.0.255 area 0
   network 10.0.13.0 0.0.0.255 area 0
  ```
- **Arista**
  ```
  router ospf 1
   network 10.0.12.0/24 area 0
   network 10.0.14.0/24 area 0
  ```
- **Juniper**
  ```
  set protocols ospf area 0 interface ge-0/0/0.0
  set protocols ospf area 0 interface ge-0/0/1.0
  ```

#### 🖧 Topology 2 Setup
| Device   | Interface | IP            | Connected To |
|----------|-----------|---------------|--------------|
| Router1  | Gi1       | 10.0.12.1/24  | Router2      |
|          | Gi2       | 10.0.13.1/24  | Router3      |
|          | Gi3       | 192.168.100.2 | tap0         |
| Router2  | Gi1       | 10.0.12.2/24  | Router1      |
|          | Gi2       | 10.0.21.1/24  | Router4      |
| Router3  | Gi1       | 10.0.13.2/24  | Router1      |
|          | Gi2       | 10.0.23.1/24  | Router4      |
| Router4  | Gi1       | 10.0.21.2/24  | Router2      |
|          | Gi2       | 10.0.23.2/24  | Router3      |

**OSPF (on all routers):**
``` 
conf t
router ospf 1
 network 10.0.12.0 0.0.0.255 area 0
 network 10.0.13.0 0.0.0.255 area 0
 network 10.0.21.0 0.0.0.255 area 0
 network 10.0.23.0 0.0.0.255 area 0
```

#### 🌐 Configure tap0 on Host (Linux)
```bash
sudo ip tuntap add dev tap0 mode tap
sudo ip addr add 192.168.100.1/24 dev tap0
sudo ip link set dev tap0 up
```
- Connect tap0 to Cloud node in GNS3
- Ping 192.168.100.2 to verify connectivity

---

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

