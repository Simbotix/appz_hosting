"""
Request new service page
"""

import frappe
from frappe import _


def get_context(context):
    """Get context for request-service page"""
    # Require login
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/request-service"
        raise frappe.Redirect

    # Get plan from query string
    plan_name = frappe.form_dict.get("plan")
    if plan_name:
        try:
            context.plan = frappe.get_doc("Service Plan", plan_name)
            template = frappe.get_doc("Deployment Template", context.plan.template)
            context.plan.template_title = template.title
            context.plan.icon = template.icon
        except frappe.DoesNotExistError:
            context.plan = None
    else:
        context.plan = None

    # Get all plans for dropdown
    context.plans = frappe.get_all(
        "Service Plan",
        filters={"enabled": 1},
        fields=["name", "title", "price_usd", "category"],
        order_by="category, sort_order"
    )

    context.no_cache = 1


@frappe.whitelist()
def submit_request(plan, domain, service_name, payment_method="razorpay"):
    """Handle service request submission"""
    if frappe.session.user == "Guest":
        frappe.throw(_("Please login to request a service"))

    # Get customer
    customer = get_or_create_customer(frappe.session.user)

    # Validate domain (basic check)
    domain = domain.strip().lower()
    if not domain or "." not in domain:
        frappe.throw(_("Please enter a valid domain"))

    # Check domain not already in use
    existing = frappe.db.exists("Hosted Service", {"domain": domain, "status": ["!=", "Cancelled"]})
    if existing:
        frappe.throw(_("This domain is already in use"))

    # Create hosted service
    service = frappe.get_doc({
        "doctype": "Hosted Service",
        "customer": customer,
        "plan": plan,
        "service_name": service_name,
        "domain": domain,
        "status": "Pending",
    })
    service.insert(ignore_permissions=True)

    # TODO: Create payment link based on payment_method
    # For now, return success and let admin approve

    frappe.db.commit()

    return {
        "success": True,
        "service": service.name,
        "message": _("Service request submitted. We will contact you shortly to complete setup.")
    }


def get_or_create_customer(user):
    """Get or create customer for user"""
    # Check if user already linked to customer
    contact = frappe.db.get_value("Contact", {"user": user}, "name")

    if contact:
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

    # Create new customer
    user_doc = frappe.get_doc("User", user)
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": user_doc.full_name or user_doc.email,
        "customer_type": "Individual",
        "customer_group": "Individual",
        "territory": "All Territories",
    })
    customer.insert(ignore_permissions=True)

    # Create contact and link
    if not contact:
        contact_doc = frappe.get_doc({
            "doctype": "Contact",
            "first_name": user_doc.first_name or user_doc.full_name,
            "last_name": user_doc.last_name,
            "user": user,
            "email_ids": [{"email_id": user_doc.email, "is_primary": 1}],
            "links": [{"link_doctype": "Customer", "link_name": customer.name}]
        })
        contact_doc.insert(ignore_permissions=True)
    else:
        # Link existing contact to customer
        frappe.get_doc({
            "doctype": "Dynamic Link",
            "parent": contact,
            "parenttype": "Contact",
            "parentfield": "links",
            "link_doctype": "Customer",
            "link_name": customer.name
        }).insert(ignore_permissions=True)

    frappe.db.commit()
    return customer.name
