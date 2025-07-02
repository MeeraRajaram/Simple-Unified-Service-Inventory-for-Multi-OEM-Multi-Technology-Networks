from flask import Flask
from blueprints.main import main_bp
from blueprints.inventory import inventory_bp
from blueprints.scan import scan_bp
from blueprints.rib import rib_bp
from blueprints.routefind import routefind_bp
from blueprints.services_physical import services_physical_bp
from blueprints.topology.topology import topology_bp
from blueprints.view import view_bp
import socket

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(inventory_bp)
app.register_blueprint(scan_bp)
app.register_blueprint(rib_bp)
app.register_blueprint(routefind_bp)
app.register_blueprint(services_physical_bp)
app.register_blueprint(topology_bp)

def find_free_port(start_port=5001, max_port=5100):
    for port in range(start_port, max_port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found in range.")

if __name__ == '__main__':
    port = find_free_port()
    print(f"Starting Flask app on port {port}")
    app.run(debug=True, port=port) 