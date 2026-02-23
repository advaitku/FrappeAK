import frappe
import requests


def execute(action_row, doc, automation):
	"""Send a WhatsApp message using the configured provider."""
	settings = frappe.get_single("AK Automation Settings")
	if not settings.whatsapp_provider:
		frappe.throw("WhatsApp provider not configured in AK Automation Settings")

	context = {
		"doc": doc,
		"frappe": frappe._dict({"utils": frappe.utils, "session": frappe.session}),
	}

	phone = frappe.render_template(action_row.wa_to or "", context).strip()
	if not phone:
		frappe.log_error("AK Automation: WhatsApp - no phone number", f"Automation: {automation.name}")
		return

	phone = _normalize_phone(phone)

	if settings.whatsapp_provider == "Meta Cloud API":
		return _send_meta(settings, action_row, phone, context)
	elif settings.whatsapp_provider == "Twilio":
		return _send_twilio(settings, action_row, phone, context)
	else:
		frappe.throw(f"Unsupported WhatsApp provider: {settings.whatsapp_provider}")


def _send_meta(settings, action_row, phone, context):
	"""Send via Meta Cloud API."""
	access_token = settings.get_password("whatsapp_access_token")
	phone_number_id = settings.whatsapp_phone_number_id

	if action_row.wa_template_name:
		payload = {
			"messaging_product": "whatsapp",
			"to": phone,
			"type": "template",
			"template": {
				"name": action_row.wa_template_name,
				"language": {"code": "en"},
			}
		}
	else:
		message = frappe.render_template(action_row.wa_message_body or "", context)
		payload = {
			"messaging_product": "whatsapp",
			"to": phone,
			"type": "text",
			"text": {"body": message},
		}

	url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
	if settings.whatsapp_api_url:
		url = f"{settings.whatsapp_api_url}/{phone_number_id}/messages"

	response = requests.post(
		url,
		headers={
			"Authorization": f"Bearer {access_token}",
			"Content-Type": "application/json",
		},
		json=payload,
		timeout=30,
	)
	response.raise_for_status()
	return f"WhatsApp sent to {phone}"


def _send_twilio(settings, action_row, phone, context):
	"""Send via Twilio."""
	try:
		from twilio.rest import Client
	except ImportError:
		frappe.throw("Twilio SDK not installed. Run: pip install twilio")

	account_sid = settings.get("whatsapp_account_sid") or ""
	auth_token = settings.get_password("whatsapp_access_token")
	from_number = settings.whatsapp_from_number

	client = Client(account_sid, auth_token)
	message_body = frappe.render_template(action_row.wa_message_body or "", context)

	message = client.messages.create(
		from_=f"whatsapp:{from_number}",
		to=f"whatsapp:{phone}",
		body=message_body,
	)
	return f"WhatsApp sent via Twilio: {message.sid}"


def _normalize_phone(phone):
	"""Normalize phone number to digits only (with leading +)."""
	phone = phone.strip()
	if phone.startswith("+"):
		return "+" + "".join(c for c in phone[1:] if c.isdigit())
	return "".join(c for c in phone if c.isdigit())
