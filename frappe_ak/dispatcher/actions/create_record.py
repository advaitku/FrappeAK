import json

import frappe


def execute(action_row, doc, automation):
	"""Create a new document of the target DocType."""
	target_doctype = action_row.target_doctype
	if not target_doctype:
		frappe.throw("Create Record action: Target DocType is required")

	context = {
		"doc": doc,
		"frappe": frappe._dict({"utils": frappe.utils, "session": frappe.session}),
	}

	# Parse the record values JSON
	values = {}
	if action_row.record_values_json:
		try:
			raw = json.loads(action_row.record_values_json)
			if isinstance(raw, dict):
				for key, val in raw.items():
					if isinstance(val, str) and "{{" in val:
						values[key] = frappe.render_template(val, context)
					else:
						values[key] = val
			elif isinstance(raw, list):
				for item in raw:
					fieldname = item.get("fieldname")
					val = item.get("value", "")
					if isinstance(val, str) and "{{" in val:
						values[fieldname] = frappe.render_template(val, context)
					else:
						values[fieldname] = val
		except (json.JSONDecodeError, TypeError):
			frappe.throw("Create Record action: Invalid record values JSON")

	values["doctype"] = target_doctype

	new_doc = frappe.get_doc(values)
	new_doc.insert(ignore_permissions=True)

	return f"Created {target_doctype}: {new_doc.name}"
