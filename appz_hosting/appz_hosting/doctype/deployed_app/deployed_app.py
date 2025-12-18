"""
Deployed App DocType - An app deployed on a customer server
"""

import frappe
from frappe.model.document import Document


class DeployedApp(Document):
    def validate(self):
        self.validate_domain()
        self.set_container_name()

    def validate_domain(self):
        """Ensure domain is lowercase"""
        if self.domain:
            self.domain = self.domain.strip().lower()

    def set_container_name(self):
        """Set container name if not set"""
        if not self.container_name:
            self.container_name = f"{self.name}-app".lower()

    def deploy(self):
        """Deploy the app to the server"""
        from appz_hosting.core.deployer import deploy_app

        result = deploy_app(self)
        if result.get("success"):
            self.status = "Running"
            self.save()
        else:
            self.status = "Error"
            self.save()
        return result

    def stop(self):
        """Stop the app container"""
        from appz_hosting.core.deployer import stop_app

        result = stop_app(self)
        if result.get("success"):
            self.status = "Stopped"
            self.save()
        return result

    def start(self):
        """Start the app container"""
        from appz_hosting.core.deployer import start_app

        result = start_app(self)
        if result.get("success"):
            self.status = "Running"
            self.save()
        return result

    def remove(self):
        """Remove the app from server"""
        from appz_hosting.core.deployer import remove_app

        result = remove_app(self)
        if result.get("success"):
            self.status = "Removed"
            self.save()
        return result

    def get_logs(self, lines=100):
        """Get container logs"""
        from appz_hosting.core.deployer import get_app_logs

        return get_app_logs(self, lines)

    def run_backup(self):
        """Run backup for this app"""
        from appz_hosting.core.backup import backup_app

        return backup_app(self)
