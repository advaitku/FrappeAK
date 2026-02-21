import frappe


def after_install():
	"""Create the AKCOM User role when the app is installed."""
	if not frappe.db.exists("Role", "AKCOM User"):
		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": "AKCOM User",
				"desk_access": 1,
				"is_custom": 1,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()
