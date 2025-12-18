import frappe
from frappe.model.document import Document


class DeploymentTemplate(Document):
    def get_compose_content(self):
        """Get the docker-compose file content"""
        if self.compose_file:
            file_doc = frappe.get_doc("File", {"file_url": self.compose_file})
            return file_doc.get_content()
        return self._get_builtin_compose()

    def get_backup_script_content(self):
        """Get the backup script content"""
        if self.backup_script:
            file_doc = frappe.get_doc("File", {"file_url": self.backup_script})
            return file_doc.get_content()
        return self._get_builtin_backup_script()

    def get_restore_script_content(self):
        """Get the restore script content"""
        if self.restore_script:
            file_doc = frappe.get_doc("File", {"file_url": self.restore_script})
            return file_doc.get_content()
        return self._get_builtin_restore_script()

    def _get_builtin_compose(self):
        """Get built-in compose file from templates directory"""
        import os
        template_path = frappe.get_app_path(
            "appz_hosting",
            "templates",
            self.category.lower().replace(" ", "-"),
            self.name,
            "docker-compose.yml"
        )
        if os.path.exists(template_path):
            with open(template_path) as f:
                return f.read()
        return None

    def _get_builtin_backup_script(self):
        """Get built-in backup script from templates directory"""
        import os
        template_path = frappe.get_app_path(
            "appz_hosting",
            "templates",
            self.category.lower().replace(" ", "-"),
            self.name,
            "backup.sh"
        )
        if os.path.exists(template_path):
            with open(template_path) as f:
                return f.read()
        return None

    def _get_builtin_restore_script(self):
        """Get built-in restore script from templates directory"""
        import os
        template_path = frappe.get_app_path(
            "appz_hosting",
            "templates",
            self.category.lower().replace(" ", "-"),
            self.name,
            "restore.sh"
        )
        if os.path.exists(template_path):
            with open(template_path) as f:
                return f.read()
        return None

    @frappe.whitelist()
    def run_test(self):
        """Run template tests"""
        from appz_hosting.core.template_tester import TemplateTest

        tester = TemplateTest(self.name)
        results = tester.run_full_test()

        self.last_test_results = frappe.as_json(results)
        if results.get("passed"):
            self.status = "Tested"
            self.tested_date = frappe.utils.today()
            self.tested_by = frappe.session.user
        else:
            self.status = "Testing"

        self.save()
        return results
