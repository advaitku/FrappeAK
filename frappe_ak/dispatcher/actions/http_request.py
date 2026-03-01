import json

import frappe
import requests


def execute(action_row, doc, automation):
	"""Make an HTTP request."""
	context = {
		"doc": doc,
		"frappe": frappe._dict({"utils": frappe.utils, "session": frappe.session}),
	}

	url = action_row.http_url or ""
	if "{{" in url:
		url = frappe.render_template(url, context)

	if not url:
		frappe.throw("HTTP Request action: URL is required")

	method = (action_row.http_method or "GET").upper()

	# Parse headers
	headers = {"Content-Type": "application/json"}
	if action_row.http_headers:
		try:
			custom_headers = json.loads(action_row.http_headers)
			if isinstance(custom_headers, dict):
				headers.update(custom_headers)
		except (json.JSONDecodeError, TypeError):
			pass

	# Parse body
	body = None
	if action_row.http_body and method in ("POST", "PUT"):
		body_str = action_row.http_body
		if "{{" in body_str:
			body_str = frappe.render_template(body_str, context)
		try:
			body = json.loads(body_str)
		except (json.JSONDecodeError, TypeError):
			body = body_str

	response = requests.request(
		method=method,
		url=url,
		headers=headers,
		json=body if isinstance(body, (dict, list)) else None,
		data=body if isinstance(body, str) else None,
		timeout=30,
	)

	return f"HTTP {method} {url} → {response.status_code}"
