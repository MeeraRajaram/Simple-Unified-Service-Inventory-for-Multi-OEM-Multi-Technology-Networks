"""
services/__init__.py
-------------------
Services package initialization for network automation web app.
This package contains modules for interacting with network devices and managing persistent data.
"""

from .rib import get_rib_entries, add_rib_entry, clear_rib_entries
from .vendor_host import get_device_info

__all__ = [
    'get_rib_entries',
    'add_rib_entry',
    'clear_rib_entries',
    'get_device_info'
] 