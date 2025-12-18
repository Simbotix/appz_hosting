"""
Service catalog page - Browse available services
"""

import frappe


def get_context(context):
    """Get context for services catalog page"""
    # Get all enabled plans grouped by category
    plans = frappe.get_all(
        "Service Plan",
        filters={"enabled": 1},
        fields=[
            "name", "title", "template", "category",
            "description", "price_usd", "price_inr", "price_btc_sats",
            "included_storage_gb", "included_bandwidth_gb"
        ],
        order_by="sort_order asc, title asc"
    )

    # Group by category
    categories = {}
    for plan in plans:
        if plan.category not in categories:
            categories[plan.category] = {
                "title": plan.category,
                "plans": []
            }

        # Get template details
        template = frappe.get_doc("Deployment Template", plan.template)
        plan.template_title = template.title
        plan.icon = template.icon
        plan.features = frappe.get_all(
            "Plan Feature",
            filters={"parent": plan.name},
            fields=["feature"],
            pluck="feature"
        )

        categories[plan.category]["plans"].append(plan)

    context.categories = categories
    context.no_cache = 1
