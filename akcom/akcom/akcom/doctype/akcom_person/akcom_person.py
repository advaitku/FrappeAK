import frappe
from frappe.model.document import Document


class AKCOMPerson(Document):
	def recalculate_bank(self):
		"""Sum all ledger entry net_amounts for this person and update bank balance."""
		total = frappe.db.sql(
			"""
			SELECT COALESCE(SUM(net_amount), 0)
			FROM `tabAKCOM Ledger Entry`
			WHERE person = %s
			""",
			(self.name,),
		)[0][0]
		self.db_set("bank", total, notify=True)


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
