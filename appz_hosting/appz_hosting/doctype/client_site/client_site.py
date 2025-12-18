"""
Client Site DocType - Represents a site/system managed for a client
"""

import frappe
from frappe.model.document import Document


class ClientSite(Document):
    def validate(self):
        self.validate_domain()

    def validate_domain(self):
        """Ensure domain is lowercase"""
        if self.domain:
            self.domain = self.domain.strip().lower()

    def update_backup_status(self, status, timestamp=None):
        """Update backup status from monitoring"""
        self.backup_status = status
        if timestamp:
            self.last_backup_date = timestamp
        self.save()

    def get_backup_history(self, limit=10):
        """Get recent backup records"""
        return frappe.get_all(
            "Service Backup",
            filters={"service": self.name},
            fields=["name", "backup_date", "status", "size_mb", "backup_type"],
            order_by="backup_date desc",
            limit=limit,
        )
