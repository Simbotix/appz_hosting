"""
Document event handlers for AppZ Hosting
"""

import frappe


def on_server_created(doc, method):
    """Handle new server creation"""
    frappe.logger().info(f"New server created: {doc.name} for {doc.customer}")

    # If status is Pending Payment, wait for payment
    # If paid, trigger provisioning
    if doc.status == "Provisioning":
        frappe.enqueue(
            "appz_hosting.core.provisioner.provision_server",
            server_name=doc.name,
        )


def on_server_updated(doc, method):
    """Handle server updates"""
    if doc.has_value_changed("status"):
        old_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None

        # Start provisioning when payment confirmed
        if old_status == "Pending Payment" and doc.status == "Provisioning":
            frappe.enqueue(
                "appz_hosting.core.provisioner.provision_server",
                server_name=doc.name,
            )


def on_app_created(doc, method):
    """Handle new app deployment"""
    frappe.logger().info(f"Deploying app: {doc.app_name} on {doc.server}")

    # Enqueue deployment
    frappe.enqueue(
        "appz_hosting.core.deployer.deploy_app_async",
        app_name=doc.name,
    )

    # Update server apps count
    server = frappe.get_doc("Customer Server", doc.server)
    server.update_apps_count()
    server.save(ignore_permissions=True)
