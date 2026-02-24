import frappe


def execute(action_row, doc, automation):
	"""Send a WhatsApp message via frappe_whatsapp's WhatsApp Message DocType."""
	if not frappe.db.exists("DocType", "WhatsApp Message"):
		frappe.throw("WhatsApp integration not available. Install the frappe_whatsapp app.")

	context = {
		"doc": doc,
		"frappe": frappe._dict({"utils": frappe.utils, "session": frappe.session}),
	}

	phone = frappe.render_template(action_row.wa_to or "", context).strip()
	if not phone:
		frappe.log_error("AK Automation: WhatsApp - no phone number", f"Automation: {automation.name}")
		return

	phone = _normalize_phone(phone)

	msg_doc = frappe.new_doc("WhatsApp Message")
	msg_doc.update({
		"type": "Outgoing",
		"to": phone,
		"reference_doctype": doc.get("doctype"),
		"reference_name": doc.get("name"),
	})

	if action_row.wa_template_name:
		msg_doc.update({
			"message_type": "Template",
			"use_template": 1,
			"template": action_row.wa_template_name,
			"content_type": "text",
			"message": "Template message",
		})
	else:
		message = frappe.render_template(action_row.wa_message_body or "", context)
		msg_doc.update({
			"content_type": "text",
			"message": message,
		})

	msg_doc.insert(ignore_permissions=True)
	return f"WhatsApp message created: {msg_doc.name}"


def _normalize_phone(phone):
	"""Normalize phone number to digits only (with leading +)."""
	phone = phone.strip()
	if phone.startswith("+"):
		return "+" + "".join(c for c in phone[1:] if c.isdigit())
	return "".join(c for c in phone if c.isdigit())
