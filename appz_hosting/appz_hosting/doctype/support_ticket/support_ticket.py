"""
Support Ticket DocType - Customer support requests
"""

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class SupportTicket(Document):
    def validate(self):
        self.set_resolved_date()

    def set_resolved_date(self):
        """Set resolved date when status changes to Resolved"""
        if self.status in ["Resolved", "Closed"] and not self.resolved_date:
            self.resolved_date = nowdate()


@frappe.whitelist()
def create_ticket(customer, subject, description, server=None, app=None, priority="Medium"):
    """Create support ticket from portal"""
    ticket = frappe.get_doc({
        "doctype": "Support Ticket",
        "customer": customer,
        "subject": subject,
        "description": description,
        "server": server,
        "app": app,
        "priority": priority,
    })
    ticket.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"success": True, "ticket": ticket.name}
