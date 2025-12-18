"""
Monitoring utilities for AppZ Hosting - Client Site monitoring
"""

import frappe
from frappe.utils import now_datetime
import requests


def check_all_client_sites():
    """Daily: Check health of all active client sites"""
    sites = frappe.get_all(
        "Client Site",
        filters={"status": "Active"},
        fields=["name", "client", "site_type", "domain", "server"],
    )

    for site in sites:
        try:
            check_site_health(site)
        except Exception as e:
            frappe.log_error(f"Failed to check site {site.name}: {e}")

    frappe.db.commit()


def check_site_health(site):
    """Check health of a single client site"""
    if not site.domain:
        return

    # Check if site is reachable
    try:
        url = f"https://{site.domain}"
        response = requests.get(url, timeout=15, verify=True)
        healthy = response.status_code < 400
    except Exception:
        healthy = False

    # Log result (could extend to store in a log table)
    if not healthy:
        frappe.log_error(
            f"Site health check failed: {site.domain}",
            f"Client Site: {site.name}",
        )

    # Update backup status if server is available
    if site.server:
        check_site_backup_status(site)


def check_site_backup_status(site):
    """Check backup status for a site"""
    # Get latest backup if using S3
    # This is a placeholder - would integrate with actual backup system
    pass


def get_client_health_summary(client_name):
    """Get health summary for all sites of a client"""
    sites = frappe.get_all(
        "Client Site",
        filters={"client": client_name, "status": "Active"},
        fields=["name", "site_name", "site_type", "domain", "backup_status", "last_backup_date"],
    )

    healthy = 0
    issues = []

    for site in sites:
        # Check if domain is accessible
        if site.domain:
            try:
                response = requests.get(f"https://{site.domain}", timeout=10)
                if response.status_code < 400:
                    healthy += 1
                else:
                    issues.append(f"{site.site_name}: HTTP {response.status_code}")
            except Exception as e:
                issues.append(f"{site.site_name}: {str(e)[:50]}")
        else:
            healthy += 1  # No domain to check

        # Check backup status
        if site.backup_status == "Failed":
            issues.append(f"{site.site_name}: Backup failed")

    return {
        "total_sites": len(sites),
        "healthy": healthy,
        "issues": issues,
        "health_percent": round(healthy / len(sites) * 100, 1) if sites else 100,
    }


def update_server_capacity(server_name):
    """Update capacity metrics for a server"""
    from appz_hosting.core.deployer import Deployer

    try:
        deployer = Deployer(server_name)

        # Get memory usage
        mem_result = deployer._exec("free -m | grep Mem | awk '{print $3}'")
        used_ram_mb = int(mem_result["stdout"].strip()) if mem_result["stdout"].strip() else 0

        # Get CPU load
        cpu_result = deployer._exec("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
        cpu_percent = float(cpu_result["stdout"].strip()) if cpu_result["stdout"].strip() else 0

        # Get disk usage
        disk_result = deployer._exec("df -BG / | tail -1 | awk '{print $3}' | tr -d 'G'")
        used_storage_gb = int(disk_result["stdout"].strip()) if disk_result["stdout"].strip() else 0

        deployer.close()

        # Update server record
        server = frappe.get_doc("AppZ Server", server_name)
        server.used_ram_gb = round(used_ram_mb / 1024, 2)
        server.used_cpu_cores = round(cpu_percent / 100 * server.total_cpu_cores, 2)
        server.used_storage_gb = used_storage_gb
        server.last_health_check = now_datetime()

        # Calculate capacity percentage (based on RAM as primary constraint)
        if server.total_ram_gb:
            server.capacity_percent = round(server.used_ram_gb / server.total_ram_gb * 100, 1)

        # Count client sites on this server
        server.service_count = frappe.db.count("Client Site", {"server": server_name, "status": "Active"})

        server.save(ignore_permissions=True)

    except Exception as e:
        frappe.log_error(f"Failed to update server capacity {server_name}: {e}")
