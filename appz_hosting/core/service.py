"""
Service lifecycle handlers for AppZ Hosting
"""

import frappe


def on_service_created(doc, method):
    """Handle new service creation"""
    # Log creation
    frappe.logger().info(f"New service created: {doc.name} for {doc.customer}")


def on_service_updated(doc, method):
    """Handle service updates"""
    # Update server capacity if status changed
    if doc.has_value_changed("status"):
        if doc.server:
            server = frappe.get_doc("AppZ Server", doc.server)
            server.update_capacity()
            server.save(ignore_permissions=True)


def on_service_deleted(doc, method):
    """Handle service deletion"""
    # Cleanup on server
    if doc.server and doc.status == "Active":
        try:
            from appz_hosting.core.deployer import Deployer
            deployer = Deployer(doc.server)
            deployer.remove_service(doc.name)
        except Exception as e:
            frappe.log_error(f"Failed to cleanup service {doc.name}: {e}")

    # Delete related records
    frappe.db.delete("Service Backup Config", {"service": doc.name})
    frappe.db.delete("Service Backup", {"service": doc.name})
    frappe.db.delete("Service Observability", {"service": doc.name})
