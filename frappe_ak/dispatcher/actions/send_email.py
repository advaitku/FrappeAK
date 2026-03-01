import frappe


def execute(action_row, doc, automation):
	"""Send an email using Frappe's built-in email infrastructure."""
	context = _build_context(doc, automation)

	to = _render(action_row.email_to, context)
	cc = _render(action_row.email_cc, context) if action_row.email_cc else None
	bcc = _render(action_row.email_bcc, context) if action_row.email_bcc else None
	subject = _render(action_row.email_subject, context)

	# Use email template if set, otherwise use body
	if action_row.email_template:
		template = frappe.get_doc("Email Template", action_row.email_template)
		message = frappe.render_template(template.response, context)
		if not subject:
			subject = frappe.render_template(template.subject, context)
	else:
		message = _render(action_row.email_body, context)

	if not to:
		frappe.log_error(title="AK Automation: Send Email - no recipients", message=f"Automation: {automation.name}")
		return

	# Attachments
	attachments = []
	if action_row.attach_print and action_row.print_format:
		attachments.append(frappe.attach_print(
			doc.doctype, doc.name,
			print_format=action_row.print_format,
		))

	# Sender
	sender = None
	if action_row.email_from:
		sender = _render(action_row.email_from, context)

	reply_to = None
	if action_row.email_reply_to:
		reply_to = _render(action_row.email_reply_to, context)

	frappe.sendmail(
		recipients=_split_emails(to),
		cc=_split_emails(cc) if cc else None,
		bcc=_split_emails(bcc) if bcc else None,
		sender=sender,
		reply_to=reply_to,
		subject=subject,
		message=message,
		reference_doctype=doc.doctype,
		reference_name=doc.name,
		attachments=attachments or None,
	)

	return f"Email sent to {to}"


def _build_context(doc, automation):
	"""Build Jinja template context."""
	return {
		"doc": doc,
		"frappe": frappe._dict({
			"utils": frappe.utils,
			"session": frappe.session,
			"get_url": frappe.utils.get_url,
		}),
		"today": frappe.utils.today(),
		"now": frappe.utils.now_datetime(),
		"user": frappe.session.user,
		"automation": automation,
	}


def _render(template_str, context):
	"""Render a Jinja template string."""
	if not template_str:
		return ""
	try:
		return frappe.render_template(template_str, context)
	except Exception:
		return template_str


def _split_emails(email_str):
	"""Split comma/newline separated emails into a list."""
	if not email_str:
		return []
	emails = []
	for part in email_str.replace("\n", ",").split(","):
		part = part.strip()
		if part:
			emails.append(part)
	return emails
