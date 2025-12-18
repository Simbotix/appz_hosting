import frappe
from frappe.model.document import Document


class AppZServer(Document):
    def validate(self):
        self.update_capacity()

    def update_capacity(self):
        """Calculate capacity based on hosted services"""
        services = frappe.get_all(
            "Hosted Service",
            filters={"server": self.name, "status": ["in", ["Active", "Provisioning"]]},
            fields=["actual_ram_mb", "actual_cpu_percent", "actual_storage_gb"]
        )

        total_ram = sum(s.actual_ram_mb or 0 for s in services) / 1024  # Convert to GB
        total_cpu = sum(s.actual_cpu_percent or 0 for s in services)
        total_storage = sum(s.actual_storage_gb or 0 for s in services)

        self.used_ram_gb = round(total_ram, 2)
        self.used_cpu_cores = round(total_cpu, 2)
        self.used_storage_gb = round(total_storage, 2)
        self.service_count = len(services)

        # Calculate overall capacity (weighted average)
        ram_pct = (total_ram / self.total_ram_gb * 100) if self.total_ram_gb else 0
        cpu_pct = (total_cpu / self.total_cpu_cores * 100) if self.total_cpu_cores else 0
        storage_pct = (total_storage / self.total_storage_gb * 100) if self.total_storage_gb else 0

        self.capacity_percent = round(max(ram_pct, cpu_pct, storage_pct), 1)

    def can_fit(self, ram_mb, cpu_cores, storage_gb):
        """Check if this server can fit additional resources"""
        new_ram_pct = ((self.used_ram_gb + ram_mb / 1024) / self.total_ram_gb * 100)
        new_cpu_pct = ((self.used_cpu_cores + cpu_cores) / self.total_cpu_cores * 100)
        new_storage_pct = ((self.used_storage_gb + storage_gb) / self.total_storage_gb * 100)

        return (
            new_ram_pct <= self.max_ram_percent and
            new_cpu_pct <= self.max_cpu_percent and
            new_storage_pct <= 90
        )

    @frappe.whitelist()
    def refresh_stats(self):
        """Refresh server stats from actual Docker usage"""
        from appz_hosting.core.deployer import Deployer

        try:
            deployer = Deployer(self.name)
            stats = deployer.get_server_stats()

            self.used_ram_gb = stats.get("used_ram_gb", 0)
            self.used_cpu_cores = stats.get("used_cpu_cores", 0)
            self.used_storage_gb = stats.get("used_storage_gb", 0)
            self.last_health_check = frappe.utils.now()
            self.save()

            return {"success": True, "stats": stats}
        except Exception as e:
            frappe.log_error(f"Failed to refresh stats for {self.name}: {e}")
            return {"success": False, "error": str(e)}
