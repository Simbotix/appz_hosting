"""
Customer Server DocType - Server owned by a customer
"""

import frappe
from frappe.model.document import Document


class CustomerServer(Document):
    def validate(self):
        self.set_pricing()
        self.update_apps_count()

    def set_pricing(self):
        """Set monthly price from plan"""
        if self.plan and not self.monthly_price:
            plan = frappe.get_doc("Server Plan", self.plan)
            self.monthly_price = plan.price_usd

    def update_apps_count(self):
        """Update count of deployed apps"""
        self.apps_count = frappe.db.count(
            "Deployed App", {"server": self.name, "status": ["!=", "Removed"]}
        )

    def provision(self):
        """Provision server via provider API"""
        from appz_hosting.core.provisioner import provision_server

        result = provision_server(self)
        if result.get("success"):
            self.status = "Active"
            self.ip_address = result.get("ip_address")
            self.provider_server_id = result.get("server_id")
            self.save()
        return result

    def destroy(self):
        """Destroy server via provider API"""
        from appz_hosting.core.provisioner import destroy_server

        result = destroy_server(self)
        if result.get("success"):
            self.status = "Terminated"
            self.save()
        return result

    def restart(self):
        """Restart server"""
        from appz_hosting.core.deployer import Deployer

        deployer = Deployer(self.name)
        result = deployer._exec("reboot")
        deployer.close()
        return result

    def get_stats(self):
        """Get current server stats"""
        from appz_hosting.core.monitoring import get_server_stats

        return get_server_stats(self.name)
