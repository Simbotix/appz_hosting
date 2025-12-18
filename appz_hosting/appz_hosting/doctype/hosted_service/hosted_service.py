import frappe
from frappe.model.document import Document


class HostedService(Document):
    def before_insert(self):
        if not self.deployment_path:
            self.deployment_path = f"/apps/{self.name}"
        if not self.container_name:
            self.container_name = f"{self.name}-app"

    def validate(self):
        # Set monthly revenue from plan
        if self.plan and not self.monthly_revenue:
            self.monthly_revenue = frappe.get_value("Service Plan", self.plan, "price_usd")

    @frappe.whitelist()
    def deploy(self):
        """Deploy this service to the assigned server"""
        from appz_hosting.core.deployer import Deployer

        if not self.server:
            # Find a server with capacity
            self.server = self._find_available_server()
            if not self.server:
                frappe.throw("No server available with sufficient capacity")

        self.status = "Provisioning"
        self.save()

        try:
            deployer = Deployer(self.server)
            result = deployer.deploy_service(self.name)

            self.status = "Active"
            self.docker_compose = result.get("compose")
            self.credentials_encrypted = frappe.utils.password.encrypt(
                frappe.as_json(result.get("credentials", {}))
            )
            self.save()

            # Create backup config if enabled
            if self.backup_enabled:
                self._create_backup_config()

            # Enable ClickStack if requested
            if self.clickstack_enabled:
                from appz_hosting.core.clickstack import enable_clickstack
                enable_clickstack(self.name)

            return {"success": True, "message": "Service deployed successfully"}

        except Exception as e:
            self.status = "Pending"
            self.last_error = str(e)
            self.error_timestamp = frappe.utils.now()
            self.save()
            frappe.log_error(f"Deployment failed for {self.name}: {e}")
            return {"success": False, "error": str(e)}

    @frappe.whitelist()
    def stop(self):
        """Stop this service"""
        from appz_hosting.core.deployer import Deployer

        if not self.server:
            frappe.throw("Service not deployed to any server")

        try:
            deployer = Deployer(self.server)
            deployer.stop_service(self.name)

            self.status = "Suspended"
            self.save()

            return {"success": True, "message": "Service stopped"}
        except Exception as e:
            frappe.log_error(f"Stop failed for {self.name}: {e}")
            return {"success": False, "error": str(e)}

    @frappe.whitelist()
    def restart(self):
        """Restart this service"""
        from appz_hosting.core.deployer import Deployer

        if not self.server:
            frappe.throw("Service not deployed to any server")

        try:
            deployer = Deployer(self.server)
            deployer.restart_service(self.name)

            return {"success": True, "message": "Service restarted"}
        except Exception as e:
            frappe.log_error(f"Restart failed for {self.name}: {e}")
            return {"success": False, "error": str(e)}

    @frappe.whitelist()
    def get_logs(self, lines=100):
        """Get service logs"""
        from appz_hosting.core.deployer import Deployer

        if not self.server:
            frappe.throw("Service not deployed to any server")

        deployer = Deployer(self.server)
        return deployer.get_logs(self.name, lines)

    @frappe.whitelist()
    def trigger_backup(self):
        """Trigger a manual backup"""
        from appz_hosting.core.backup import BackupManager

        manager = BackupManager(self.name)
        return manager.run_backup()

    def _find_available_server(self):
        """Find a server with capacity for this service"""
        plan = frappe.get_doc("Service Plan", self.plan)
        template = frappe.get_doc("Deployment Template", plan.template)

        servers = frappe.get_all(
            "AppZ Server",
            filters={"status": "Active"},
            fields=["name"]
        )

        for server in servers:
            server_doc = frappe.get_doc("AppZ Server", server.name)
            if server_doc.can_fit(
                template.min_ram_mb,
                template.min_cpu,
                template.min_storage_gb
            ):
                return server.name

        return None

    def _create_backup_config(self):
        """Create backup configuration for this service"""
        if not frappe.db.exists("Service Backup Config", {"service": self.name}):
            config = frappe.get_doc({
                "doctype": "Service Backup Config",
                "service": self.name,
                "enabled": 1,
                "backup_frequency": "Daily",
                "backup_time": "03:00",
                "retention_days": 30,
                "storage_type": "S3",
                "s3_bucket": frappe.conf.get("hetzner_s3_bucket", "appz-backups"),
                "s3_prefix": f"services/{self.name}/"
            })
            config.insert(ignore_permissions=True)
