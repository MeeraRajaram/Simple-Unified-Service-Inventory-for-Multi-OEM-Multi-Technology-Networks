import sqlite3
from ncclient import manager
from ncclient.transport.errors import AuthenticationError
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'push_data.db')

class NetconfManager:
    def __init__(self, host, username, password, port=830, hostkey_verify=False):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.hostkey_verify = hostkey_verify

    def connect(self):
        """Establish NETCONF connection"""
        try:
            conn = manager.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                hostkey_verify=self.hostkey_verify
            )
            return conn
        except AuthenticationError:
            raise Exception("Authentication failed. Check credentials.")
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")

    def get_config(self, filter_xml):
        """Retrieve running config with filter"""
        with self.connect() as conn:
            return conn.get_config(source='running', filter=filter_xml)

    def edit_config(self, config_xml):
        """Apply configuration changes"""
        with self.connect() as conn:
            conn.edit_config(target='running', config=config_xml)

def get_netconf_managers_from_db():
    """Parse push_data.db and return a list of NetconfManager instances for each router."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT router_loopback_ip, netconf_username, netconf_password FROM push_data')
    managers = []
    for row in c.fetchall():
        host, username, password = row
        if host and username and password:
            managers.append(NetconfManager(host=host, username=username, password=password, port=830))
    conn.close()
    return managers 