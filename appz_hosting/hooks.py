app_name = "appz_hosting"
app_title = "AppZ Hosting"
app_publisher = "Simbotix"
app_description = "Cloud Partner - Internal tooling for managing SMB clients (1-50 person teams)"
app_email = "rajesh@simbotix.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/appz_hosting/css/appz_hosting.css"
# app_include_js = "/assets/appz_hosting/js/appz_hosting.js"

# include js, css files in header of web template
# web_include_css = "/assets/appz_hosting/css/appz_hosting.css"
# web_include_js = "/assets/appz_hosting/js/appz_hosting.js"

# include custom scss in every website theme (without signing in)
# website_theme_scss = "appz_hosting/public/scss/website"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#     "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Scheduled Tasks
# ---------------

scheduler_events = {
    "hourly": [
        "appz_hosting.core.backup.run_scheduled_backups",
    ],
    "daily": [
        "appz_hosting.core.monitoring.check_all_client_sites",
        "appz_hosting.core.backup.cleanup_failed_backups",
    ],
    "monthly": [
        "appz_hosting.appz_hosting.doctype.client.client.reset_all_monthly_hours",
    ],
}

# Jinja
# -----

# add methods and filters to jinja environment
# jinja = {
#     "methods": "appz_hosting.utils.jinja_methods",
#     "filters": "appz_hosting.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "appz_hosting.install.before_install"
after_install = "appz_hosting.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "appz_hosting.uninstall.before_uninstall"
# after_uninstall = "appz_hosting.uninstall.after_uninstall"

# Document Events
# ---------------

doc_events = {
    "Client": {
        "after_insert": "appz_hosting.core.client_events.on_client_created",
        "on_update": "appz_hosting.core.client_events.on_client_updated",
    },
    "Support Entry": {
        "after_insert": "appz_hosting.core.client_events.on_support_entry_created",
    },
}

# Testing
# -------

# before_tests = "appz_hosting.install.before_tests"

# Overriding Methods
# ------------------

# override_whitelisted_methods = {
#     "frappe.desk.doctype.event.event.get_events": "appz_hosting.event.get_events"
# }

# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#     "Task": "appz_hosting.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Fixtures
# --------

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "AppZ Hosting"]],
    },
    {
        "dt": "Property Setter",
        "filters": [["module", "=", "AppZ Hosting"]],
    },
]
