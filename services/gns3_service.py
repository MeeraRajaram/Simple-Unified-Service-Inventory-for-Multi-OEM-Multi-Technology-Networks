import requests

def connect_to_gns3(gns3_server, project_name):
    try:
        # Check GNS3 server connection
        response = requests.get(f"{gns3_server}/v2/version")
        if response.status_code != 200:
            return False, "❌ Could not connect to GNS3 server."
        # Get list of projects
        projects_resp = requests.get(f"{gns3_server}/v2/projects")
        if projects_resp.status_code != 200:
            return False, "❌ Could not retrieve projects from GNS3 server."
        projects = projects_resp.json()
        # Check if project name exists
        found = any(p.get('name') == project_name for p in projects)
        if found:
            return True, f"✅ Connected to GNS3 server. Project '{project_name}' found."
        else:
            return False, f"❌ Project '{project_name}' not found on GNS3 server."
    except requests.exceptions.RequestException as e:
        return False, f"❌ Connection error: {e}" 