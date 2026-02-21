import frappe


def execute_action(action_row, doc, automation):
	"""Dispatch an action row to the appropriate handler."""
	action_type = action_row.action_type

	handler_map = {
		"Send Email": "automation_ak.dispatcher.actions.send_email.execute",
		"Send WhatsApp": "automation_ak.dispatcher.actions.send_whatsapp.execute",
		"Update Fields": "automation_ak.dispatcher.actions.update_fields.execute",
		"Field Formulas": "automation_ak.dispatcher.actions.update_fields.execute",
		"Create Record": "automation_ak.dispatcher.actions.create_record.execute",
		"Create Todo": "automation_ak.dispatcher.actions.create_todo.execute",
		"Create Event": "automation_ak.dispatcher.actions.create_event.execute",
		"HTTP Request": "automation_ak.dispatcher.actions.http_request.execute",
		"Run Script": "automation_ak.dispatcher.actions.run_script.execute",
	}

	handler_path = handler_map.get(action_type)
	if not handler_path:
		frappe.throw(f"Unknown action type: {action_type}")

	handler = frappe.get_attr(handler_path)
	return handler(action_row, doc, automation)
