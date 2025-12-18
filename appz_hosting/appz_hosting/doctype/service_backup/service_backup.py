import frappe
from frappe.model.document import Document


class ServiceBackup(Document):
    @frappe.whitelist()
    def restore(self):
        """Restore service from this backup"""
        from appz_hosting.core.backup import BackupManager

        if self.status != "Completed":
            frappe.throw("Cannot restore from incomplete backup")

        if not self.can_restore:
            frappe.throw("This backup cannot be restored")

        manager = BackupManager(self.service)
        result = manager.restore_backup(self.name)

        if result.get("success"):
            self.last_restore_date = frappe.utils.now()
            self.save()

        return result
