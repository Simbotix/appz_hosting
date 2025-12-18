"""
Backup System for AppZ Hosting

Handles automated backups to S3-compatible storage.
"""

import frappe
import boto3
import os
from datetime import datetime, timedelta


class BackupManager:
    """Handles backup and restore operations"""

    def __init__(self, service_name):
        self.service = frappe.get_doc("Hosted Service", service_name)
        self.config = self._get_or_create_config()
        self.s3 = self._get_s3_client()

    def _get_or_create_config(self):
        """Get or create backup config for service"""
        config_name = frappe.db.get_value(
            "Service Backup Config",
            {"service": self.service.name}
        )
        if config_name:
            return frappe.get_doc("Service Backup Config", config_name)
        return None

    def _get_s3_client(self):
        """Get S3 client"""
        return boto3.client(
            "s3",
            endpoint_url=frappe.conf.get("hetzner_s3_endpoint"),
            aws_access_key_id=frappe.conf.get("hetzner_s3_access_key"),
            aws_secret_access_key=frappe.conf.get("hetzner_s3_secret_key"),
        )

    def run_backup(self):
        """Execute backup for service"""
        if not self.config:
            frappe.throw("No backup configuration found for this service")

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_id = f"{self.service.name}-{timestamp}"

        # Create backup record
        backup = frappe.get_doc({
            "doctype": "Service Backup",
            "service": self.service.name,
            "backup_config": self.config.name,
            "timestamp": datetime.now(),
            "status": "Running",
        })
        backup.insert(ignore_permissions=True)
        frappe.db.commit()

        try:
            from appz_hosting.core.deployer import Deployer
            deployer = Deployer(self.service.server)

            # Get template for backup paths
            plan = frappe.get_doc("Service Plan", self.service.plan)
            template = frappe.get_doc("Deployment Template", plan.template)

            # Run backup script
            backup_script = self._get_backup_script(template)
            local_backup_path = f"/tmp/backups/{backup_id}"

            result = deployer._exec(f"""
                mkdir -p {local_backup_path}
                export SERVICE_ID={self.service.name}
                export DATA_PATH=/apps/{self.service.name}
                export BACKUP_PATH={local_backup_path}
                {backup_script}
            """, timeout=600)

            if result["exit_code"] != 0:
                raise Exception(f"Backup script failed: {result['stderr']}")

            # Get backup size
            size_result = deployer._exec(f"du -sm {local_backup_path} | cut -f1")
            size_mb = int(size_result["stdout"].strip() or 0)

            # List backup files
            files_result = deployer._exec(f"ls {local_backup_path}")
            files = files_result["stdout"].strip().split("\n")

            # Upload to S3
            s3_prefix = f"services/{self.service.name}/{timestamp}/"
            for filename in files:
                if not filename:
                    continue
                local_file = f"{local_backup_path}/{filename}"
                s3_key = f"{s3_prefix}{filename}"

                # Stream upload via SSH
                self._upload_to_s3_via_ssh(deployer, local_file, s3_key)

            # Cleanup local backup
            deployer._exec(f"rm -rf {local_backup_path}")

            # Update backup record
            backup.status = "Completed"
            backup.s3_path = f"s3://{self.config.s3_bucket}/{s3_prefix}"
            backup.size_mb = size_mb
            backup.file_count = len([f for f in files if f])
            backup.manifest = frappe.as_json({
                "files": files,
                "timestamp": timestamp,
                "template": template.name
            })
            backup.can_restore = 1
            backup.save(ignore_permissions=True)

            # Update config
            self.config.last_backup = datetime.now()
            self.config.last_backup_status = "Success"
            self.config.last_backup_size_mb = size_mb
            self.config.total_backup_count = (self.config.total_backup_count or 0) + 1
            self.config.save(ignore_permissions=True)

            frappe.db.commit()

            # Prune old backups
            self._prune_old_backups()

            return {"success": True, "backup": backup.name, "size_mb": size_mb}

        except Exception as e:
            backup.status = "Failed"
            backup.error_log = str(e)
            backup.save(ignore_permissions=True)

            self.config.last_backup_status = "Failed"
            self.config.save(ignore_permissions=True)

            frappe.db.commit()
            frappe.log_error(f"Backup failed for {self.service.name}: {e}")

            return {"success": False, "error": str(e)}

    def _get_backup_script(self, template):
        """Get backup script for template"""
        # Try to get from template
        script = template.get_backup_script_content()
        if script:
            return script

        # Default backup script
        return '''
# Generic backup script
cd ${DATA_PATH}

# Find and dump databases
if docker ps --format '{{.Names}}' | grep -q "${SERVICE_ID}-db"; then
    # Check if MySQL/MariaDB
    if docker exec ${SERVICE_ID}-db mysql --version 2>/dev/null; then
        docker exec ${SERVICE_ID}-db mysqldump -u root -p${DB_ROOT_PASSWORD} --all-databases > ${BACKUP_PATH}/database.sql
    fi
    # Check if PostgreSQL
    if docker exec ${SERVICE_ID}-db psql --version 2>/dev/null; then
        docker exec ${SERVICE_ID}-db pg_dumpall -U postgres > ${BACKUP_PATH}/database.sql
    fi
fi

# Backup data directory
tar -czf ${BACKUP_PATH}/data.tar.gz -C ${DATA_PATH} . --exclude='mysql' --exclude='postgres'

# Create manifest
echo '{"service": "'${SERVICE_ID}'", "timestamp": "'$(date -Iseconds)'"}' > ${BACKUP_PATH}/manifest.json
'''

    def _upload_to_s3_via_ssh(self, deployer, remote_path, s3_key):
        """Upload file from remote server to S3"""
        # For simplicity, download locally then upload to S3
        # In production, consider using s3cmd on the server directly
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            local_tmp = tmp.name

        try:
            # Download from server
            ssh = deployer._connect()
            sftp = ssh.open_sftp()
            sftp.get(remote_path, local_tmp)
            sftp.close()

            # Upload to S3
            self.s3.upload_file(local_tmp, self.config.s3_bucket, s3_key)
        finally:
            if os.path.exists(local_tmp):
                os.remove(local_tmp)

    def restore_backup(self, backup_name):
        """Restore service from backup"""
        backup = frappe.get_doc("Service Backup", backup_name)

        if backup.status != "Completed":
            frappe.throw("Cannot restore from incomplete backup")

        try:
            from appz_hosting.core.deployer import Deployer
            deployer = Deployer(self.service.server)

            # Create restore directory
            restore_path = f"/tmp/restore/{backup.name}"
            deployer._exec(f"mkdir -p {restore_path}")

            # Download from S3
            s3_prefix = backup.s3_path.replace(f"s3://{self.config.s3_bucket}/", "")
            objects = self.s3.list_objects_v2(
                Bucket=self.config.s3_bucket,
                Prefix=s3_prefix
            )

            for obj in objects.get("Contents", []):
                filename = obj["Key"].split("/")[-1]
                self._download_from_s3_to_ssh(
                    deployer,
                    obj["Key"],
                    f"{restore_path}/{filename}"
                )

            # Get template for restore script
            plan = frappe.get_doc("Service Plan", self.service.plan)
            template = frappe.get_doc("Deployment Template", plan.template)

            # Run restore script
            restore_script = self._get_restore_script(template)
            result = deployer._exec(f"""
                export SERVICE_ID={self.service.name}
                export DATA_PATH=/apps/{self.service.name}
                export BACKUP_PATH={restore_path}
                {restore_script}
            """, timeout=600)

            # Cleanup
            deployer._exec(f"rm -rf {restore_path}")

            if result["exit_code"] != 0:
                raise Exception(f"Restore failed: {result['stderr']}")

            return {"success": True, "message": "Restore completed"}

        except Exception as e:
            frappe.log_error(f"Restore failed for {self.service.name}: {e}")
            return {"success": False, "error": str(e)}

    def _get_restore_script(self, template):
        """Get restore script for template"""
        script = template.get_restore_script_content()
        if script:
            return script

        # Default restore script
        return '''
# Generic restore script
cd ${DATA_PATH}

# Stop app container
docker stop ${SERVICE_ID}-app || true

# Restore database
if [ -f ${BACKUP_PATH}/database.sql ]; then
    if docker ps --format '{{.Names}}' | grep -q "${SERVICE_ID}-db"; then
        # MySQL/MariaDB
        if docker exec ${SERVICE_ID}-db mysql --version 2>/dev/null; then
            docker exec -i ${SERVICE_ID}-db mysql -u root -p${DB_ROOT_PASSWORD} < ${BACKUP_PATH}/database.sql
        fi
        # PostgreSQL
        if docker exec ${SERVICE_ID}-db psql --version 2>/dev/null; then
            docker exec -i ${SERVICE_ID}-db psql -U postgres < ${BACKUP_PATH}/database.sql
        fi
    fi
fi

# Restore data
if [ -f ${BACKUP_PATH}/data.tar.gz ]; then
    tar -xzf ${BACKUP_PATH}/data.tar.gz -C ${DATA_PATH}
fi

# Restart app
docker start ${SERVICE_ID}-app
'''

    def _download_from_s3_to_ssh(self, deployer, s3_key, remote_path):
        """Download file from S3 to remote server"""
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            local_tmp = tmp.name

        try:
            # Download from S3
            self.s3.download_file(self.config.s3_bucket, s3_key, local_tmp)

            # Upload to server
            ssh = deployer._connect()
            sftp = ssh.open_sftp()
            sftp.put(local_tmp, remote_path)
            sftp.close()
        finally:
            if os.path.exists(local_tmp):
                os.remove(local_tmp)

    def _prune_old_backups(self):
        """Delete backups older than retention period"""
        if not self.config:
            return

        cutoff = datetime.now() - timedelta(days=self.config.retention_days)

        old_backups = frappe.get_all(
            "Service Backup",
            filters={
                "service": self.service.name,
                "timestamp": ["<", cutoff],
                "status": "Completed"
            },
            pluck="name"
        )

        for backup_name in old_backups:
            self._delete_backup(backup_name)

    def _delete_backup(self, backup_name):
        """Delete a backup from S3 and database"""
        backup = frappe.get_doc("Service Backup", backup_name)

        try:
            # Delete from S3
            if backup.s3_path:
                prefix = backup.s3_path.replace(f"s3://{self.config.s3_bucket}/", "")
                objects = self.s3.list_objects_v2(
                    Bucket=self.config.s3_bucket,
                    Prefix=prefix
                )
                for obj in objects.get("Contents", []):
                    self.s3.delete_object(
                        Bucket=self.config.s3_bucket,
                        Key=obj["Key"]
                    )
        except Exception as e:
            frappe.log_error(f"Failed to delete S3 objects: {e}")

        # Delete record
        frappe.delete_doc("Service Backup", backup_name, force=True)


# Scheduled tasks
def run_scheduled_backups():
    """Run by scheduler every hour"""
    current_hour = datetime.now().strftime("%H:00")

    # Daily backups
    configs = frappe.get_all(
        "Service Backup Config",
        filters={
            "enabled": 1,
            "backup_frequency": "Daily",
            "backup_time": ["like", f"{current_hour}%"]
        },
        pluck="service"
    )

    for service in configs:
        try:
            manager = BackupManager(service)
            manager.run_backup()
        except Exception as e:
            frappe.log_error(f"Scheduled backup failed for {service}: {e}")


def cleanup_failed_backups():
    """Cleanup failed backup records older than 7 days"""
    cutoff = datetime.now() - timedelta(days=7)

    old_failed = frappe.get_all(
        "Service Backup",
        filters={
            "status": "Failed",
            "timestamp": ["<", cutoff]
        },
        pluck="name"
    )

    for backup_name in old_failed:
        frappe.delete_doc("Service Backup", backup_name, force=True)


def prune_old_backups():
    """Prune old backups for all services"""
    configs = frappe.get_all(
        "Service Backup Config",
        filters={"enabled": 1},
        pluck="service"
    )

    for service in configs:
        try:
            manager = BackupManager(service)
            manager._prune_old_backups()
        except Exception as e:
            frappe.log_error(f"Prune failed for {service}: {e}")


def test_random_backups():
    """Weekly: Test restore of random backups"""
    import random

    # Get 10% of services (min 1)
    services = frappe.get_all(
        "Hosted Service",
        filters={"status": "Active", "backup_enabled": 1},
        pluck="name"
    )

    sample_size = max(1, len(services) // 10)
    sample = random.sample(services, min(sample_size, len(services)))

    for service in sample:
        try:
            # Get latest backup
            backup = frappe.get_all(
                "Service Backup",
                filters={"service": service, "status": "Completed"},
                order_by="timestamp desc",
                limit=1,
                pluck="name"
            )

            if backup:
                # TODO: Implement restore test on test server
                frappe.get_doc("Service Backup", backup[0]).db_set(
                    "restore_tested", 1
                )
        except Exception as e:
            frappe.log_error(f"Backup test failed for {service}: {e}")
