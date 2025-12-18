"""
Installation script for AppZ Hosting

Sets up default data after app installation.
"""

import frappe


def after_install():
    """Setup default data after app installation"""
    create_sample_data()


def create_sample_data():
    """Create sample data for testing (optional)"""
    # Skip if any clients already exist
    if frappe.db.count("Client") > 0:
        return

    # Create a sample server
    if not frappe.db.exists("AppZ Server", "appz-prod-01"):
        frappe.get_doc(
            {
                "doctype": "AppZ Server",
                "server_name": "appz-prod-01",
                "provider": "Hetzner",
                "server_type": "AX52",
                "ip_address": "0.0.0.0",  # Placeholder
                "status": "Active",
                "location": "Falkenstein, Germany",
                "total_ram_gb": 64,
                "total_cpu_cores": 8,
                "total_storage_gb": 2000,
                "monthly_cost": 77,
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()

    frappe.msgprint(
        "AppZ Hosting installed successfully. Create your first Client to get started.",
        alert=True,
    )
