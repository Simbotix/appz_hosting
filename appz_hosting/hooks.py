app_name = "appz_hosting"
app_title = "AppZ Hosting"
app_publisher = "Simbotix"
app_description = "White-label cloud server management with one-click app deployment"
app_email = "rajesh@simbotix.com"
app_license = "MIT"

# Website Routes
website_route_rules = [
    {"from_route": "/my-servers", "to_route": "my-servers"},
    {"from_route": "/my-servers/<path:server>", "to_route": "server-detail"},
    {"from_route": "/order-server", "to_route": "order-server"},
    {"from_route": "/deploy-app", "to_route": "deploy-app"},
    {"from_route": "/support", "to_route": "support"},
]

# Scheduled Tasks
scheduler_events = {
    "cron": {
        "*/5 * * * *": [
            "appz_hosting.core.monitoring.health_check_all_servers",
        ],
    },
    "hourly": [
        "appz_hosting.core.backup.run_scheduled_backups",
    ],
    "daily": [
        "appz_hosting.core.monitoring.collect_server_stats",
        "appz_hosting.core.backup.cleanup_old_backups",
    ],
}

# Installation
after_install = "appz_hosting.install.after_install"

# Document Events
doc_events = {
    "Customer Server": {
        "after_insert": "appz_hosting.core.events.on_server_created",
        "on_update": "appz_hosting.core.events.on_server_updated",
    },
    "Deployed App": {
        "after_insert": "appz_hosting.core.events.on_app_created",
    },
}

# Fixtures
fixtures = [
    {
        "dt": "Server Plan",
        "filters": [["enabled", "=", 1]],
    },
    {
        "dt": "App Template",
        "filters": [["enabled", "=", 1]],
    },
]
