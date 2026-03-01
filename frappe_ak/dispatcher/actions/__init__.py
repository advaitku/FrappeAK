import frappe
from importlib import import_module


ACTION_MODULE_MAP = {
	"Send Email": "frappe_ak.dispatcher.actions.send_email",
	"Send WhatsApp": "frappe_ak.dispatcher.actions.send_whatsapp",
	"Update Fields": "frappe_ak.dispatcher.actions.update_fields",
	"Create Record": "frappe_ak.dispatcher.actions.create_record",
	"Create Todo": "frappe_ak.dispatcher.actions.create_todo",
	"Create Event": "frappe_ak.dispatcher.actions.create_event",
	"HTTP Request": "frappe_ak.dispatcher.actions.http_request",
	"Run Script": "frappe_ak.dispatcher.actions.run_script",
}


def execute_action(action_row, doc, automation):
	"""Dispatch an action row to the correct handler module."""
	action_type = action_row.action_type
	module_path = ACTION_MODULE_MAP.get(action_type)

	if not module_path:
		frappe.throw(f"Unknown action type: {action_type}")

	module = import_module(module_path)
	return module.execute(action_row, doc, automation)
