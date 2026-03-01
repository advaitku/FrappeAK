import json

import frappe

from frappe_ak.dispatcher.formula import resolve_value


def execute(action_row, doc, automation):
	"""Update fields on the current document based on field_updates_json or AK Field Update rows."""
	updates = _get_updates(action_row, automation)

	if not updates:
		return "No field updates defined"

	changed_fields = {}

	for update in updates:
		fieldname = update.get("target_field") or update.get("fieldname")
		value_type = update.get("value_type", "Static Value")

		resolved = resolve_value(value_type, update, doc)
		changed_fields[fieldname] = resolved

	if not changed_fields:
		return "No fields to update"

	# Use db_set to avoid retriggering doc_events
	if automation.trigger_type in ("On Create", "On Update (includes Create)"):
		for fieldname, value in changed_fields.items():
			frappe.db.set_value(
				doc.doctype, doc.name, fieldname, value,
				update_modified=False,
			)
		# Also update the in-memory doc so subsequent actions see the change
		for fieldname, value in changed_fields.items():
			_set_field(doc, fieldname, value)
	else:
		# For before_save, just set on the doc object — it will be saved automatically
		for fieldname, value in changed_fields.items():
			_set_field(doc, fieldname, value)

	field_names = ", ".join(changed_fields.keys())
	return f"Updated fields: {field_names}"


def _set_field(doc, fieldname, value):
	"""Set a field on the doc, handling both Document and plain dict objects."""
	set_fn = getattr(doc, "set", None)
	if callable(set_fn):
		doc.set(fieldname, value)
	else:
		doc[fieldname] = value


def _get_updates(action_row, automation):
	"""Get the list of field updates from JSON or from AK Field Update child table."""
	# First try JSON blob on the action row
	if action_row.field_updates_json:
		try:
			return json.loads(action_row.field_updates_json)
		except (json.JSONDecodeError, TypeError):
			pass

	# Fallback: look for AK Field Update rows on the parent automation
	if hasattr(automation, "field_updates") and automation.field_updates:
		action_idx = action_row.idx
		return [
			u.as_dict()
			for u in automation.field_updates
			if u.parent_action_idx == action_idx
		]

	return []
