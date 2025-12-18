"""
Client event handlers for AppZ Hosting
"""

import frappe
from frappe import _


def on_client_created(doc, method):
    """Handle new client creation"""
    # Log the event
    frappe.logger().info(f"New client created: {doc.company_name}")

    # Send notification (could be extended to use n8n webhook)
    frappe.publish_realtime(
        "new_client",
        {"client": doc.name, "company": doc.company_name, "package": doc.package},
    )


def on_client_updated(doc, method):
    """Handle client updates"""
    # Check if status changed
    if doc.has_value_changed("status"):
        old_status = doc.get_doc_before_save().status if doc.get_doc_before_save() else None
        frappe.logger().info(f"Client {doc.name} status changed from {old_status} to {doc.status}")

        # If churned, could trigger cleanup workflow
        if doc.status == "Churned":
            frappe.publish_realtime(
                "client_churned",
                {"client": doc.name, "company": doc.company_name},
            )


def on_support_entry_created(doc, method):
    """Handle new support entry"""
    # Check if client is approaching overage
    client = frappe.get_doc("Client", doc.client)

    if client.support_hours_remaining and client.support_hours_remaining < 1:
        # Less than 1 hour remaining
        frappe.msgprint(
            _(f"Warning: {client.company_name} has less than 1 hour of support remaining this month."),
            indicator="orange",
            alert=True,
        )

    if client.support_hours_remaining and client.support_hours_remaining < 0:
        # In overage
        frappe.msgprint(
            _(f"Note: {client.company_name} is in overage hours. Extra hours will be billed at $75/hr."),
            indicator="red",
            alert=True,
        )
