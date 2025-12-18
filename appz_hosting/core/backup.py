"""
Backup System for AppZ Hosting

Handles backup verification and status tracking for client sites.
Most ERPNext sites use Frappe Press's built-in backup system.
This module tracks backup status and provides alerts.
"""

import frappe
from frappe.utils import now_datetime, add_days, getdate
from datetime import datetime, timedelta


def run_scheduled_backups():
    """Run by scheduler every hour - check backup status for client sites"""
    sites = frappe.get_all(
        "Client Site",
        filters={"status": "Active", "backup_enabled": 1},
        fields=["name", "site_type", "last_backup_date", "backup_location"],
    )

    for site in sites:
        try:
            check_backup_status(site)
        except Exception as e:
            frappe.log_error(f"Backup check failed for {site.name}: {e}")

    frappe.db.commit()


def check_backup_status(site):
    """Check if a site's backup is current"""
    site_doc = frappe.get_doc("Client Site", site.name)

    # Determine if backup is stale (more than 24 hours old)
    if site_doc.last_backup_date:
        hours_since_backup = (now_datetime() - site_doc.last_backup_date).total_seconds() / 3600

        if hours_since_backup > 48:
            site_doc.backup_status = "Failed"
        elif hours_since_backup > 24:
            site_doc.backup_status = "Warning"
        else:
            site_doc.backup_status = "OK"
    else:
        site_doc.backup_status = "Unknown"

    site_doc.save(ignore_permissions=True)

    # Alert if backup is failing
    if site_doc.backup_status == "Failed":
        client = frappe.get_doc("Client", site_doc.client)
        frappe.log_error(
            f"Backup stale for client site: {site_doc.site_name} ({client.company_name})",
            "Backup Alert",
        )


def cleanup_failed_backups():
    """Cleanup old error logs related to backups"""
    cutoff = add_days(getdate(), -7)

    # Clean up old backup-related error logs
    frappe.db.delete(
        "Error Log",
        {"creation": ["<", cutoff], "method": ["like", "%backup%"]},
    )
    frappe.db.commit()


def get_client_backup_summary(client_name):
    """Get backup summary for all sites of a client"""
    sites = frappe.get_all(
        "Client Site",
        filters={"client": client_name, "backup_enabled": 1},
        fields=["site_name", "site_type", "backup_status", "last_backup_date"],
    )

    ok_count = sum(1 for s in sites if s.backup_status == "OK")
    warning_count = sum(1 for s in sites if s.backup_status == "Warning")
    failed_count = sum(1 for s in sites if s.backup_status == "Failed")

    return {
        "total_sites": len(sites),
        "ok": ok_count,
        "warning": warning_count,
        "failed": failed_count,
        "sites": sites,
    }


def update_backup_timestamp(site_name, timestamp=None):
    """Update last backup timestamp for a site (called by external systems)"""
    site = frappe.get_doc("Client Site", site_name)
    site.last_backup_date = timestamp or now_datetime()
    site.backup_status = "OK"
    site.save(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def manual_backup_check(site_name):
    """Manually trigger backup check for a site"""
    site = frappe.get_doc("Client Site", site_name)
    check_backup_status(site.as_dict())
    frappe.msgprint(f"Backup status: {site.backup_status}")
