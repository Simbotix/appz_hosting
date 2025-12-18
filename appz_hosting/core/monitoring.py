"""
Monitoring utilities for AppZ Hosting
"""

import frappe


def update_all_service_stats():
    """Daily: Update stats for all active services"""
    services = frappe.get_all(
        "Hosted Service",
        filters={"status": "Active"},
        fields=["name", "server"]
    )

    # Group by server to minimize SSH connections
    servers = {}
    for service in services:
        if service.server not in servers:
            servers[service.server] = []
        servers[service.server].append(service.name)

    for server_name, service_names in servers.items():
        try:
            update_server_services(server_name, service_names)
        except Exception as e:
            frappe.log_error(f"Failed to update stats for server {server_name}: {e}")


def update_server_services(server_name, service_names):
    """Update stats for all services on a server"""
    from appz_hosting.core.deployer import Deployer

    deployer = Deployer(server_name)

    for service_name in service_names:
        try:
            # Get Docker stats
            stats = deployer.get_stats(service_name)

            # Parse stats (format: "name|mem|cpu")
            if stats:
                for line in stats.strip().split("\n"):
                    if not line:
                        continue
                    parts = line.split("|")
                    if len(parts) >= 3:
                        # Parse memory (e.g., "256MiB / 512MiB")
                        mem_str = parts[1].split("/")[0].strip()
                        if "GiB" in mem_str:
                            mem_mb = float(mem_str.replace("GiB", "")) * 1024
                        elif "MiB" in mem_str:
                            mem_mb = float(mem_str.replace("MiB", ""))
                        else:
                            mem_mb = 0

                        # Parse CPU (e.g., "5.25%")
                        cpu_str = parts[2].strip().replace("%", "")
                        cpu_percent = float(cpu_str) if cpu_str else 0

                        # Update service
                        frappe.db.set_value("Hosted Service", service_name, {
                            "actual_ram_mb": int(mem_mb),
                            "actual_cpu_percent": cpu_percent,
                        }, update_modified=False)

            # Get disk usage
            disk_result = deployer._exec(f"du -sm /apps/{service_name} 2>/dev/null | cut -f1")
            if disk_result["stdout"].strip():
                storage_mb = int(disk_result["stdout"].strip())
                frappe.db.set_value("Hosted Service", service_name, {
                    "actual_storage_gb": round(storage_mb / 1024, 2),
                    "storage_used_gb": round(storage_mb / 1024, 2),
                }, update_modified=False)

        except Exception as e:
            frappe.log_error(f"Failed to update stats for {service_name}: {e}")

    deployer.close()
    frappe.db.commit()

    # Update server capacity
    server = frappe.get_doc("AppZ Server", server_name)
    server.update_capacity()
    server.last_health_check = frappe.utils.now()
    server.save(ignore_permissions=True)


def check_service_health(service_name):
    """Check if a service is healthy"""
    service = frappe.get_doc("Hosted Service", service_name)
    plan = frappe.get_doc("Service Plan", service.plan)
    template = frappe.get_doc("Deployment Template", plan.template)

    import requests
    try:
        url = f"https://{service.domain}{template.healthcheck_path}"
        response = requests.get(url, timeout=10, verify=True)
        return response.status_code < 400
    except:
        return False


def get_service_uptime(service_name, days=30):
    """Calculate uptime percentage for a service"""
    # This would integrate with ClickStack or uptime monitoring
    # For now, return default
    return 99.9
