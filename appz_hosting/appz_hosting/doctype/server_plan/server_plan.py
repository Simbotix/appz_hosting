"""
Server Plan DocType - Pricing plans for servers
"""

import frappe
from frappe.model.document import Document


class ServerPlan(Document):
    def validate(self):
        self.calculate_margin()

    def calculate_margin(self):
        """Calculate margin percentage"""
        if self.cost_eur and self.price_usd:
            # Rough EUR to USD conversion
            cost_usd = float(self.cost_eur) * 1.1
            margin = ((float(self.price_usd) - cost_usd) / float(self.price_usd)) * 100
            self.margin_percent = round(margin, 1)
