import frappe
from frappe.model.document import Document


class AKAutomation(Document):
	def validate(self):
		if not self.actions:
			frappe.throw("At least one action is required.")

	def on_update(self):
		self.clear_automation_cache()

	def on_trash(self):
		self.clear_automation_cache()

	def clear_automation_cache(self):
		"""Clear the Redis cache for automation lookups."""
		frappe.cache().delete_keys("ak_automations:*")
