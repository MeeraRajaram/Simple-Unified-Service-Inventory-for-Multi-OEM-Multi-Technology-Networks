# GNS3 WebApp

This is a web-based network topology and protocol visualization tool built with Flask.

## Project Structure

```
webapp/
│
├── app.py                  # Main Flask app entry point
├── config.py               # (Optional) Configuration settings
├── requirements.txt        # Python dependencies
│
├── blueprints/
│   ├── __init__.py
│   ├── topology/
│   │   ├── __init__.py
│   │   ├── topology.py         # Topology routes and visualization logic
│   │   ├── protocol_utils.py   # Protocol/OSPF DB logic (new)
│   └── rib/
│       ├── __init__.py
│       └── rib.py
│
├── services/
│   ├── __init__.py
│   ├── db.py
│   ├── netconf_service.py
│   └── ports_protocols.py
│
├── topo/
│   ├── __init__.py
│   ├── topo_connections.py
│   ├── topo_inip.py
│   └── ...
│
├── pathfinder/
│   ├── __init__.py
│   ├── path.py
│   └── find.py
│
├── templates/
│   └── topology/
│       ├── topology_view.html
│       ├── protocol_topology_view.html
│       └── ...
│
├── static/
│   └── ... (css, js, images)
│
├── protodb
├── proto_routes.db
├── ospfdb
├── inip.db
├── rib_db.sqlite3
└── directconndb
```

## Main Modules

- **app.py**: Flask app entry point, registers blueprints.
- **blueprints/topology/topology.py**: Topology routes and visualization logic.
- **blueprints/topology/protocol_utils.py**: Protocol/OSPF DB logic (building proto_routes.db and ospfdb).
- **services/**: Utility modules for DB, NETCONF, and protocol helpers.
- **topo/**: Topology extraction and connection logic.
- **pathfinder/**: Pathfinding and network graph logic.
- **templates/**: Jinja2 HTML templates for the web UI.
- **static/**: Static assets (CSS, JS, images).

## Navigation Tips

- **Routes and Views**: Start in `blueprints/topology/topology.py` for all topology-related endpoints.
- **Protocol/OSPF DB Logic**: See `blueprints/topology/protocol_utils.py`.
- **Database Helpers**: See `services/db.py`.
- **Topology Extraction**: See `topo/topo_connections.py` and `topo/topo_inip.py`.
- **Pathfinding**: See `pathfinder/path.py`.

## How to Add New Features

- Add new routes in the appropriate blueprint (e.g., `topology.py`).
- Add new protocol/OSPF logic in `protocol_utils.py`.
- Add new templates in `templates/topology/`.

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run the app: `python3 app.py`
3. Visit `http://localhost:5000/topology` in your browser.

---

For more details, see comments and docstrings in each module. 