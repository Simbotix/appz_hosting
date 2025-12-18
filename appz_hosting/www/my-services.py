"""
Customer portal - My Services page
"""

import frappe


def get_context(context):
    """Get context for my-services page"""
    # Require login
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/my-services"
        raise frappe.Redirect

    customer = get_customer_for_user(frappe.session.user)

    if not customer:
        context.services = []
        context.no_customer = True
        return

    # Get customer's services
    context.services = frappe.get_all(
        "Hosted Service",
        filters={
            "customer": customer,
            "status": ["!=", "Cancelled"]
        },
        fields=[
            "name", "service_name", "domain", "status",
            "plan", "storage_used_gb", "uptime_percent", "created_on",
            "clickstack_enabled", "backup_enabled"
        ],
        order_by="created_on desc"
    )

    # Enrich with plan details
    for service in context.services:
        plan = frappe.get_doc("Service Plan", service.plan)
        service.plan_title = plan.title
        service.plan_category = plan.category
        service.price = plan.price_usd

        # Get template icon
        template = frappe.get_doc("Deployment Template", plan.template)
        service.icon = template.icon

    context.total_monthly = sum(s.price or 0 for s in context.services)
    context.no_cache = 1


def get_customer_for_user(user):
    """Get customer linked to this user via Contact"""
    contact = frappe.db.get_value("Contact", {"user": user}, "name")
    if not contact:
        return None

    links = frappe.get_all(
        "Dynamic Link",
        filters={
            "parent": contact,
            "parenttype": "Contact",
            "link_doctype": "Customer"
        },
        fields=["link_name"]
    )

    if links:
        return links[0].link_name

    return None
