import frappe


@frappe.whitelist()
def get_doctype_fields(doctype):
	"""Return fields of a DocType for UI dropdowns (field pickers)."""
	meta = frappe.get_meta(doctype)
	fields = []
	for df in meta.fields:
		if df.fieldtype not in (
			"Section Break", "Column Break", "Tab Break", "HTML",
			"Table", "Table MultiSelect", "Fold",
		):
			fields.append({
				"fieldname": df.fieldname,
				"label": df.label or df.fieldname,
				"fieldtype": df.fieldtype,
				"options": df.options,
				"reqd": df.reqd,
			})
	return fields


@frappe.whitelist()
def get_field_options(doctype, fieldname):
	"""Return valid options for a Select field on a DocType."""
	meta = frappe.get_meta(doctype)
	df = meta.get_field(fieldname)
	if df and df.fieldtype == "Select" and df.options:
		return [opt for opt in df.options.split("\n") if opt]
	return []


@frappe.whitelist()
def get_operators_for_field(doctype, fieldname):
	"""Return valid operators based on field type."""
	meta = frappe.get_meta(doctype)
	df = meta.get_field(fieldname)

	if not df:
		return _text_operators()

	fieldtype = df.fieldtype

	if fieldtype in ("Int", "Float", "Currency", "Percent"):
		return _numeric_operators()
	elif fieldtype in ("Date", "Datetime"):
		return _date_operators()
	elif fieldtype == "Select":
		return _select_operators()
	elif fieldtype in ("Link", "Dynamic Link"):
		return _link_operators()
	elif fieldtype == "Check":
		return _check_operators()
	else:
		return _text_operators()


def _text_operators():
	return [
		"is", "is not", "contains", "does not contain",
		"starts with", "ends with", "is empty", "is not empty",
		"has changed", "has changed to", "has changed from",
	]


def _numeric_operators():
	return [
		"=", "!=", ">", "<", ">=", "<=", "between",
		"is empty", "is not empty", "has changed",
	]


def _date_operators():
	return [
		"is", "is not", "before", "after", "between",
		"is today", "is tomorrow", "is yesterday",
		"less than days ago", "more than days ago",
		"less than days later", "more than days later",
		"is empty", "is not empty",
	]


def _select_operators():
	return [
		"is", "is not", "has changed", "has changed to", "has changed from",
	]


def _link_operators():
	return [
		"is", "is not", "is empty", "is not empty", "has changed",
	]


def _check_operators():
	return ["is", "is not"]


@frappe.whitelist()
def run_button_automation(automation_name, doctype, docname):
	"""Execute a button-triggered (Macro) automation on a specific document."""
	automation = frappe.get_doc("AK Automation", automation_name)

	if not automation.enabled:
		frappe.throw("This automation is disabled.")
	if automation.trigger_type != "Macro (Button)":
		frappe.throw("This automation is not a button/macro trigger.")

	doc = frappe.get_doc(doctype, docname)
	doc.check_permission("write")

	from frappe_ak.dispatcher.conditions import evaluate_conditions
	if not evaluate_conditions(automation, doc):
		return {"status": "skipped", "message": "Conditions not met."}

	from frappe_ak.dispatcher.actions import execute_action
	results = []
	for action_row in automation.actions:
		if action_row.enabled:
			result = execute_action(action_row, doc, automation)
			results.append(result)

	return {"status": "ok", "message": f"Automation '{automation.title}' executed successfully."}


@frappe.whitelist()
def test_automation(automation_name, docname=None):
	"""Dry-run an automation to preview what would happen."""
	automation = frappe.get_doc("AK Automation", automation_name)

	if docname:
		doc = frappe.get_doc(automation.reference_doctype, docname)
	else:
		latest = frappe.get_list(
			automation.reference_doctype,
			limit=1,
			order_by="modified desc",
			pluck="name",
		)
		if not latest:
			frappe.throw(f"No documents found for {automation.reference_doctype}")
		doc = frappe.get_doc(automation.reference_doctype, latest[0])

	from frappe_ak.dispatcher.conditions import evaluate_conditions
	conditions_met = evaluate_conditions(automation, doc)

	return {
		"document": doc.name,
		"conditions_met": conditions_met,
		"actions_count": len([a for a in automation.actions if a.enabled]),
		"message": "Conditions met — actions would execute." if conditions_met else "Conditions NOT met — automation would be skipped.",
	}


@frappe.whitelist()
def get_button_automations(doctype):
	"""Return all active button/macro automations for a DocType."""
	return frappe.get_list("AK Automation",
		filters={
			"reference_doctype": doctype,
			"trigger_type": "Macro (Button)",
			"enabled": 1,
		},
		fields=["name", "title", "button_label"],
	)


@frappe.whitelist()
def test_whatsapp_connection():
	"""Test that WhatsApp API credentials are valid."""
	settings = frappe.get_single("AK Automation Settings")
	if not settings.whatsapp_provider:
		return {"success": False, "error": "No WhatsApp provider configured"}

	try:
		if settings.whatsapp_provider == "Meta Cloud API":
			import requests
			token = settings.get_password("whatsapp_access_token")
			phone_id = settings.whatsapp_phone_number_id
			url = f"https://graph.facebook.com/v18.0/{phone_id}"
			resp = requests.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=10)
			if resp.status_code == 200:
				return {"success": True}
			return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
		return {"success": False, "error": "Connection test not implemented for this provider"}
	except Exception as e:
		return {"success": False, "error": str(e)}
