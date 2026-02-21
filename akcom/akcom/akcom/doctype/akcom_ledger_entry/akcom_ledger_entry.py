import frappe
from frappe.model.document import Document


class AKCOMLedgerEntry(Document):
	def before_save(self):
		"""Compute net_amount from the entry type and amount details."""
		if self.entry_type == "ADD":
			if self.amount_type == "Lumpsum":
				self.computed_add_amount = self.lumpsum_amount or 0
			elif self.amount_type == "Percentage":
				base = self.base_amount or 0
				pct = self.percentage or 0
				self.computed_add_amount = base * (pct / 100)
			else:
				self.computed_add_amount = 0
			self.net_amount = self.computed_add_amount
		elif self.entry_type == "SUBTRACT":
			self.net_amount = -(self.expense_amount or 0)
		else:
			self.net_amount = 0

	def on_update(self):
		self._update_person_bank()

	def on_trash(self):
		self._update_person_bank()

	def _update_person_bank(self):
		if self.person:
			person = frappe.get_doc("AKCOM Person", self.person)
			person.recalculate_bank()


def has_permission(doc, ptype, user):
	"""Block all users who do not have the AKCOM User role."""
	if frappe.db.exists("Has Role", {"parent": user, "role": "AKCOM User"}):
		return True
	return False


def get_permission_query_conditions(user):
	"""Return 1=0 for non-AKCOM users so list views show nothing."""
	if frappe.db.exists("Has Role", {"parent": user, "role": "AKCOM User"}):
		return ""
	return "1=0"
