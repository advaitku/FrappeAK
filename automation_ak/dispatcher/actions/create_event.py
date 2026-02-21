import json

import frappe
from frappe.utils import add_days, today, now_datetime


def execute(action_row, doc, automation):
	"""Create a calendar Event linked to the triggering document."""
	context = {
		"doc": doc,
		"frappe": frappe._dict({"utils": frappe.utils, "session": frappe.session}),
	}

	config = {}
	if action_row.record_values_json:
		try:
			config = json.loads(action_row.record_values_json)
		except (json.JSONDecodeError, TypeError):
			pass

	subject = config.get("subject", f"{automation.title} - {doc.name}")
	if isinstance(subject, str) and "{{" in subject:
		subject = frappe.render_template(subject, context)

	starts_on = config.get("starts_on", now_datetime())
	ends_on = config.get("ends_on")
	event_type = config.get("event_type", "Private")

	event = frappe.get_doc({
		"doctype": "Event",
		"subject": subject,
		"starts_on": starts_on,
		"ends_on": ends_on,
		"event_type": event_type,
	})
	event.insert(ignore_permissions=True)

	return f"Created Event: {event.name}"
