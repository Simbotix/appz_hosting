"""
App Template DocType - Docker compose templates for one-click deployment
"""

import frappe
from frappe.model.document import Document
from jinja2 import Template


class AppTemplate(Document):
    def validate(self):
        pass

    def render_compose(self, variables):
        """Render docker-compose with variables"""
        if not self.docker_compose:
            return None
        return Template(self.docker_compose).render(**variables)

    def render_env(self, variables):
        """Render environment template with variables"""
        if not self.env_template:
            return ""
        return Template(self.env_template).render(**variables)

    def get_backup_script(self):
        """Get backup script content"""
        return self.backup_script or ""

    def get_restore_script(self):
        """Get restore script content"""
        return self.restore_script or ""
