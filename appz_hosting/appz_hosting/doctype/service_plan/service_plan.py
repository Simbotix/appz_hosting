import frappe
from frappe.model.document import Document


class ServicePlan(Document):
    def validate(self):
        self.calculate_margin()

    def calculate_margin(self):
        """Calculate margin percentage"""
        if self.price_usd and self.your_cost_eur:
            # Convert EUR to USD (approximate)
            cost_usd = self.your_cost_eur * 1.1
            self.margin_percent = ((self.price_usd - cost_usd) / self.price_usd) * 100
