"""
Support Entry DocType - Track support hours for clients
"""

import frappe
from frappe.model.document import Document
from frappe.utils import get_first_day, get_last_day, nowdate


class SupportEntry(Document):
    def validate(self):
        self.validate_hours()

    def validate_hours(self):
        """Validate hours is reasonable"""
        if self.hours <= 0:
            frappe.throw("Hours must be greater than 0")
        if self.hours > 8:
            frappe.msgprint("Note: Logging more than 8 hours for a single entry", indicator="orange")

    def after_insert(self):
        """Update client's monthly hours after insert"""
        self.update_client_hours()

    def on_update(self):
        """Update client's monthly hours on update"""
        self.update_client_hours()

    def on_trash(self):
        """Update client's monthly hours on delete"""
        self.update_client_hours(subtract=True)

    def update_client_hours(self, subtract=False):
        """Update the client's support_hours_used_this_month"""
        if not self.billable:
            return

        client = frappe.get_doc("Client", self.client)

        # Get current month's billable hours
        first_day = get_first_day(nowdate())
        last_day = get_last_day(nowdate())

        total_hours = frappe.db.sql(
            """
            SELECT COALESCE(SUM(hours), 0) as total
            FROM `tabSupport Entry`
            WHERE client = %s
            AND date BETWEEN %s AND %s
            AND billable = 1
        """,
            (self.client, first_day, last_day),
        )[0][0]

        client.support_hours_used_this_month = total_hours
        client.calculate_support_hours_remaining()
        client.save(ignore_permissions=True)


def get_monthly_report(client_name, month=None, year=None):
    """Generate monthly support report for a client"""
    from frappe.utils import getdate

    if not month:
        month = getdate(nowdate()).month
    if not year:
        year = getdate(nowdate()).year

    first_day = f"{year}-{month:02d}-01"
    last_day = get_last_day(first_day)

    entries = frappe.get_all(
        "Support Entry",
        filters={
            "client": client_name,
            "date": ["between", [first_day, last_day]],
        },
        fields=["date", "hours", "category", "description", "billable", "billed"],
        order_by="date asc",
    )

    client = frappe.get_doc("Client", client_name)

    total_hours = sum(e.hours for e in entries)
    billable_hours = sum(e.hours for e in entries if e.billable)
    included = client.support_hours_included or 0
    overage = max(0, billable_hours - included)

    return {
        "client": client_name,
        "month": month,
        "year": year,
        "entries": entries,
        "total_hours": total_hours,
        "billable_hours": billable_hours,
        "included_hours": included,
        "overage_hours": overage,
        "overage_cost": overage * 75,  # $75/hr overage rate
    }
