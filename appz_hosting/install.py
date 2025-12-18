import frappe


def after_install():
    """Setup default data after app installation"""
    create_default_templates()
    create_default_plans()


def create_default_templates():
    """Create default deployment templates"""
    templates = [
        {
            "name": "wordpress",
            "title": "WordPress",
            "version": "6.4",
            "category": "CMS",
            "status": "Tested",
            "description": "Full WordPress installation with MariaDB and Redis cache",
            "min_ram_mb": 512,
            "min_cpu": 0.25,
            "min_storage_gb": 5,
            "recommended_ram_mb": 1024,
            "internal_port": 80,
            "healthcheck_path": "/wp-admin/install.php",
            "supports_clickstack": 1,
            "supports_backup": 1,
            "backup_paths": '["/var/www/html/wp-content", "/var/lib/mysql"]',
        },
        {
            "name": "n8n",
            "title": "n8n",
            "version": "latest",
            "category": "Automation",
            "status": "Tested",
            "description": "Workflow automation tool with PostgreSQL backend",
            "min_ram_mb": 1024,
            "min_cpu": 0.5,
            "min_storage_gb": 5,
            "recommended_ram_mb": 2048,
            "internal_port": 5678,
            "healthcheck_path": "/healthz",
            "supports_clickstack": 1,
            "supports_backup": 1,
            "backup_paths": '["/home/node/.n8n", "/var/lib/postgresql/data"]',
        },
        {
            "name": "ghost",
            "title": "Ghost",
            "version": "5",
            "category": "CMS",
            "status": "Tested",
            "description": "Modern publishing platform for blogs",
            "min_ram_mb": 512,
            "min_cpu": 0.25,
            "min_storage_gb": 5,
            "recommended_ram_mb": 1024,
            "internal_port": 2368,
            "healthcheck_path": "/ghost/api/v4/admin/site/",
            "supports_clickstack": 1,
            "supports_backup": 1,
            "backup_paths": '["/var/lib/ghost/content", "/var/lib/mysql"]',
        },
    ]

    for template_data in templates:
        if not frappe.db.exists("Deployment Template", template_data["name"]):
            doc = frappe.get_doc({
                "doctype": "Deployment Template",
                **template_data
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()


def create_default_plans():
    """Create default service plans"""
    plans = [
        {
            "name": "wordpress-starter",
            "title": "WordPress Starter",
            "template": "wordpress",
            "category": "CMS",
            "description": "Perfect for blogs and small business sites",
            "price_usd": 15,
            "price_inr": 1200,
            "price_btc_sats": 15000,
            "billing_cycle": "Monthly",
            "your_cost_eur": 2.50,
            "included_storage_gb": 5,
            "included_bandwidth_gb": 100,
        },
        {
            "name": "n8n-starter",
            "title": "n8n Automation",
            "template": "n8n",
            "category": "Automation",
            "description": "Workflow automation for your business",
            "price_usd": 25,
            "price_inr": 2000,
            "price_btc_sats": 25000,
            "billing_cycle": "Monthly",
            "your_cost_eur": 4,
            "included_storage_gb": 5,
            "included_bandwidth_gb": 50,
        },
        {
            "name": "ghost-starter",
            "title": "Ghost Blog",
            "template": "ghost",
            "category": "CMS",
            "description": "Modern publishing platform",
            "price_usd": 15,
            "price_inr": 1200,
            "price_btc_sats": 15000,
            "billing_cycle": "Monthly",
            "your_cost_eur": 2.50,
            "included_storage_gb": 5,
            "included_bandwidth_gb": 100,
        },
    ]

    for plan_data in plans:
        if not frappe.db.exists("Service Plan", plan_data["name"]):
            doc = frappe.get_doc({
                "doctype": "Service Plan",
                **plan_data
            })
            doc.insert(ignore_permissions=True)
            frappe.db.commit()
