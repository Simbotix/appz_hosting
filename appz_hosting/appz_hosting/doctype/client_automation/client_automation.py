"""
Client Automation DocType - Track n8n workflows for clients
"""

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class ClientAutomation(Document):
    def validate(self):
        pass

    def log_run(self, success=True, error_message=None):
        """Log a workflow run"""
        self.last_run = now_datetime()
        self.run_count = (self.run_count or 0) + 1

        if not success:
            self.error_count = (self.error_count or 0) + 1
            self.last_error = error_message
            self.last_error_date = now_datetime()
            self.status = "Error"
        elif self.status == "Error":
            self.status = "Active"

        self.save(ignore_permissions=True)

    def pause(self):
        """Pause the automation"""
        self.status = "Paused"
        self.save()
        # TODO: Call n8n API to deactivate workflow

    def activate(self):
        """Activate the automation"""
        self.status = "Active"
        self.save()
        # TODO: Call n8n API to activate workflow


def get_client_automations_summary(client_name):
    """Get summary of automations for a client"""
    automations = frappe.get_all(
        "Client Automation",
        filters={"client": client_name},
        fields=["workflow_name", "status", "trigger_type", "run_count", "error_count", "last_run"],
    )

    active = sum(1 for a in automations if a.status == "Active")
    errors = sum(1 for a in automations if a.status == "Error")
    total_runs = sum(a.run_count or 0 for a in automations)

    return {
        "automations": automations,
        "total": len(automations),
        "active": active,
        "errors": errors,
        "total_runs": total_runs,
    }
