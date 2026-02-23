import json

import frappe


def execute(action_row, doc, automation):
	"""Create a ToDo linked to the triggering document."""
	context = {
		"doc": doc,
		"frappe": frappe._dict({"utils": frappe.utils, "session": frappe.session}),
	}

	# Parse config from record_values_json or use defaults
	config = {}
	if action_row.record_values_json:
		try:
			config = json.loads(action_row.record_values_json)
		except (json.JSONDecodeError, TypeError):
			pass

	description = config.get("description", f"Follow up on {doc.doctype}: {doc.name}")
	if isinstance(description, str) and "{{" in description:
		description = frappe.render_template(description, context)

	assigned_to = config.get("assigned_to", frappe.session.user)
	if isinstance(assigned_to, str) and "{{" in assigned_to:
		assigned_to = frappe.render_template(assigned_to, context)

	priority = config.get("priority", "Medium")
	date = config.get("date", frappe.utils.today())

	todo = frappe.get_doc({
		"doctype": "ToDo",
		"description": description,
		"allocated_to": assigned_to,
		"reference_type": doc.doctype,
		"reference_name": doc.name,
		"priority": priority,
		"date": date,
	})
	todo.insert(ignore_permissions=True)

	return f"Created ToDo: {todo.name}"
