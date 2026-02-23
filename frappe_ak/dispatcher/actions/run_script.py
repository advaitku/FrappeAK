import frappe


def execute(action_row, doc, automation):
	"""Execute a custom Python script with restricted access."""
	script = action_row.script_code
	if not script:
		return "No script code provided"

	# Build a safe execution context
	context = {
		"doc": doc,
		"frappe": frappe,
		"automation": automation,
	}

	try:
		frappe.safe_eval(script, eval_globals=context, eval_locals={})
	except SyntaxError:
		# If safe_eval fails (multi-line), use restricted exec
		exec_globals = {
			"__builtins__": {},
			"doc": doc,
			"frappe": frappe,
			"automation": automation,
			"str": str,
			"int": int,
			"float": float,
			"bool": bool,
			"list": list,
			"dict": dict,
			"len": len,
			"range": range,
			"enumerate": enumerate,
			"isinstance": isinstance,
			"print": frappe.log_error,
		}
		exec(compile(script, f"<AK Automation: {automation.name}>", "exec"), exec_globals)

	return "Script executed"
