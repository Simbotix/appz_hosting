"""
AI Capacity Advisor for AppZ Hosting

Provides intelligent capacity planning and resource estimation.
"""

import frappe

# Resource estimates per template (ram_mb, cpu_cores, storage_gb)
RESOURCE_ESTIMATES = {
    "wordpress": (512, 0.25, 5),
    "ghost": (512, 0.25, 5),
    "n8n": (1024, 0.5, 5),
    "plausible": (1024, 0.5, 10),
    "umami": (512, 0.25, 5),
    "strapi": (512, 0.25, 5),
    "directus": (512, 0.25, 5),
    "nocodb": (512, 0.25, 5),
    "gitea": (512, 0.25, 10),
    "minio": (512, 0.25, 50),
    "postgres": (512, 0.25, 5),
    "mariadb": (512, 0.25, 5),
    "redis": (256, 0.1, 1),
    "uptime-kuma": (256, 0.1, 1),
    "static-site": (128, 0.1, 1),
    "erpnext": (4096, 1.0, 20),
    "frappe-crm": (2048, 0.5, 10),
}

# Hetzner server specs
HETZNER_SERVERS = [
    ("CX22", 4, 2, 40, 4),      # 4GB, 2 CPU, 40GB, €4/mo
    ("CX32", 8, 4, 80, 7),      # 8GB, 4 CPU, 80GB, €7/mo
    ("CX42", 16, 8, 160, 14),   # 16GB, 8 CPU, 160GB, €14/mo
    ("CX52", 32, 16, 320, 28),  # 32GB, 16 CPU, 320GB, €28/mo
    ("AX41", 64, 8, 1000, 49),  # 64GB, 8 CPU, 1TB, €49/mo
    ("AX52", 64, 8, 2000, 77),  # 64GB, 8 CPU, 2TB, €77/mo
    ("AX102", 128, 16, 3840, 130),  # 128GB, 16 CPU, 3.8TB, €130/mo
]


class CapacityAdvisor:
    """AI-powered capacity planning"""

    def __init__(self, server_name):
        self.server = frappe.get_doc("AppZ Server", server_name)
        self.existing_services = self._get_existing_services()

    def _get_existing_services(self):
        """Get all running services on this server"""
        return frappe.get_all(
            "Hosted Service",
            filters={
                "server": self.server.name,
                "status": ["in", ["Active", "Provisioning"]]
            },
            fields=["name", "plan", "actual_ram_mb", "actual_cpu_percent", "actual_storage_gb"]
        )

    def get_current_usage(self):
        """Get current resource usage on server"""
        total_ram = 0
        total_cpu = 0
        total_storage = 0

        for service in self.existing_services:
            if service.actual_ram_mb:
                total_ram += service.actual_ram_mb
                total_cpu += service.actual_cpu_percent or 0
                total_storage += service.actual_storage_gb or 0
            else:
                # Use estimates
                plan = frappe.get_doc("Service Plan", service.plan)
                template = frappe.get_doc("Deployment Template", plan.template)
                estimate = RESOURCE_ESTIMATES.get(
                    template.name,
                    (template.min_ram_mb, template.min_cpu, template.min_storage_gb)
                )
                total_ram += estimate[0]
                total_cpu += estimate[1]
                total_storage += estimate[2]

        ram_percent = (total_ram / (self.server.total_ram_gb * 1024)) * 100 if self.server.total_ram_gb else 0
        cpu_percent = (total_cpu / self.server.total_cpu_cores) * 100 if self.server.total_cpu_cores else 0
        storage_percent = (total_storage / self.server.total_storage_gb) * 100 if self.server.total_storage_gb else 0

        return {
            "ram_mb": total_ram,
            "ram_percent": round(ram_percent, 1),
            "cpu_cores": total_cpu,
            "cpu_percent": round(cpu_percent, 1),
            "storage_gb": total_storage,
            "storage_percent": round(storage_percent, 1),
            "service_count": len(self.existing_services)
        }

    def can_fit(self, template_name, count=1):
        """Check if N instances of a template can fit"""
        estimate = RESOURCE_ESTIMATES.get(template_name, (512, 0.25, 5))
        required_ram = estimate[0] * count
        required_cpu = estimate[1] * count
        required_storage = estimate[2] * count

        current = self.get_current_usage()

        new_ram_percent = ((current["ram_mb"] + required_ram) / (self.server.total_ram_gb * 1024)) * 100
        new_cpu_percent = ((current["cpu_cores"] + required_cpu) / self.server.total_cpu_cores) * 100
        new_storage_percent = ((current["storage_gb"] + required_storage) / self.server.total_storage_gb) * 100

        can_fit = (
            new_ram_percent <= self.server.max_ram_percent and
            new_cpu_percent <= self.server.max_cpu_percent and
            new_storage_percent <= 90
        )

        limiting_factor = None
        if new_ram_percent > self.server.max_ram_percent:
            limiting_factor = "RAM"
        elif new_cpu_percent > self.server.max_cpu_percent:
            limiting_factor = "CPU"
        elif new_storage_percent > 90:
            limiting_factor = "Storage"

        return {
            "can_fit": can_fit,
            "after_deployment": {
                "ram_percent": round(new_ram_percent, 1),
                "cpu_percent": round(new_cpu_percent, 1),
                "storage_percent": round(new_storage_percent, 1),
            },
            "thresholds": {
                "max_ram_percent": self.server.max_ram_percent,
                "max_cpu_percent": self.server.max_cpu_percent,
            },
            "limiting_factor": limiting_factor
        }

    def suggest_capacity(self, template_name):
        """How many of this template can we fit?"""
        count = 0
        while count < 100:
            result = self.can_fit(template_name, count + 1)
            if not result["can_fit"]:
                break
            count += 1

        return {
            "template": template_name,
            "max_count": count,
            "current_usage": self.get_current_usage(),
            "estimate_per_instance": RESOURCE_ESTIMATES.get(template_name, (512, 0.25, 5))
        }

    def suggest_all_capacities(self):
        """Get capacity for all common templates"""
        templates = ["wordpress", "n8n", "ghost", "plausible", "static-site", "erpnext"]
        return {t: self.suggest_capacity(t)["max_count"] for t in templates}


def suggest_server_for_workload(workload):
    """
    Suggest optimal server for a given workload.

    Args:
        workload: List of tuples [(template_name, count), ...]

    Returns:
        Recommended server configuration
    """
    total_ram = 0
    total_cpu = 0
    total_storage = 0

    for template_name, count in workload:
        estimate = RESOURCE_ESTIMATES.get(template_name, (512, 0.25, 5))
        total_ram += estimate[0] * count
        total_cpu += estimate[1] * count
        total_storage += estimate[2] * count

    # Add 25% headroom
    total_ram *= 1.25
    total_cpu *= 1.25
    total_storage *= 1.25

    # Find suitable server
    for name, ram_gb, cpu, storage_gb, price in HETZNER_SERVERS:
        if (total_ram <= ram_gb * 1024 * 0.8 and
            total_cpu <= cpu * 0.7 and
            total_storage <= storage_gb * 0.9):
            return {
                "recommended_server": name,
                "price_eur": price,
                "specs": {"ram_gb": ram_gb, "cpu_cores": cpu, "storage_gb": storage_gb},
                "workload_requires": {
                    "ram_mb": int(total_ram),
                    "cpu_cores": round(total_cpu, 2),
                    "storage_gb": int(total_storage)
                },
                "utilization_after": {
                    "ram_percent": round((total_ram / (ram_gb * 1024)) * 100, 1),
                    "cpu_percent": round((total_cpu / cpu) * 100, 1),
                    "storage_percent": round((total_storage / storage_gb) * 100, 1)
                }
            }

    return {"error": "Workload too large for single server, consider splitting"}


def find_best_server(template_name):
    """Find the best available server for a template"""
    servers = frappe.get_all(
        "AppZ Server",
        filters={"status": "Active"},
        fields=["name"]
    )

    for server in servers:
        advisor = CapacityAdvisor(server.name)
        if advisor.can_fit(template_name)["can_fit"]:
            return server.name

    return None


# API endpoints
@frappe.whitelist()
def check_capacity(server, template, count=1):
    """Check if server can fit template instances"""
    advisor = CapacityAdvisor(server)
    return advisor.can_fit(template, int(count))


@frappe.whitelist()
def get_server_capacity(server):
    """Get current server capacity"""
    advisor = CapacityAdvisor(server)
    return {
        "usage": advisor.get_current_usage(),
        "capacities": advisor.suggest_all_capacities()
    }


@frappe.whitelist()
def suggest_server(workload_json):
    """
    Suggest server for workload.

    Args:
        workload_json: JSON string like '[["wordpress", 5], ["n8n", 2]]'
    """
    import json
    workload = json.loads(workload_json)
    return suggest_server_for_workload(workload)
