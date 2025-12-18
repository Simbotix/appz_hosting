"""
Client DocType - Represents a cloud partner client (1-50 person teams)
"""

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, add_months, getdate


class Client(Document):
    def validate(self):
        self.validate_team_size()
        self.set_package_defaults()
        self.calculate_support_hours_remaining()

    def validate_team_size(self):
        """Validate team size is within 1-50 range"""
        if self.team_size < 1:
            frappe.throw("Team size must be at least 1")
        if self.team_size > 50:
            frappe.throw("Team size cannot exceed 50. For larger teams, contact us for enterprise pricing.")

    def set_package_defaults(self):
        """Set default values based on package"""
        package_defaults = {
            "Starter": {"support_hours_included": 4, "response_sla": "24 hours"},
            "Growth": {"support_hours_included": 8, "response_sla": "12 hours"},
            "Business": {"support_hours_included": 16, "response_sla": "4 hours"},
        }
        if self.package and self.package in package_defaults:
            defaults = package_defaults[self.package]
            if not self.support_hours_included:
                self.support_hours_included = defaults["support_hours_included"]
            if not self.response_sla:
                self.response_sla = defaults["response_sla"]

    def calculate_support_hours_remaining(self):
        """Calculate remaining support hours for current month"""
        self.support_hours_remaining = (
            (self.support_hours_included or 0) - (self.support_hours_used_this_month or 0)
        )

    def get_monthly_support_summary(self):
        """Get support entries for current month"""
        from frappe.utils import get_first_day, get_last_day

        first_day = get_first_day(nowdate())
        last_day = get_last_day(nowdate())

        entries = frappe.get_all(
            "Support Entry",
            filters={
                "client": self.name,
                "date": ["between", [first_day, last_day]],
            },
            fields=["date", "hours", "description", "category", "billable"],
        )

        total_hours = sum(e.hours for e in entries)
        billable_hours = sum(e.hours for e in entries if e.billable)

        return {
            "entries": entries,
            "total_hours": total_hours,
            "billable_hours": billable_hours,
            "included_hours": self.support_hours_included,
            "overage_hours": max(0, billable_hours - (self.support_hours_included or 0)),
        }

    def reset_monthly_hours(self):
        """Reset support hours for new month (called by scheduler)"""
        self.support_hours_used_this_month = 0
        self.calculate_support_hours_remaining()
        self.save()


def reset_all_monthly_hours():
    """Scheduler job to reset monthly hours on 1st of month"""
    clients = frappe.get_all("Client", filters={"status": "Active"})
    for client in clients:
        doc = frappe.get_doc("Client", client.name)
        doc.reset_monthly_hours()
