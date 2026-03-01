import time
import traceback

import frappe

from frappe_ak.dispatcher.conditions import evaluate_conditions


# Map Frappe doc events to our trigger types
EVENT_MAP = {
	"after_insert": "On Create",
	"on_update": "On Update (includes Create)",
	"before_save": "On Update (includes Create)",
	"on_submit": "On Update (includes Create)",
	"on_cancel": "On Update (includes Create)",
}


def handle_event(doc, method):
	"""Wildcard doc_events handler. Finds matching automations and runs them."""
	# Skip our own DocTypes to avoid loops
	if doc.doctype in ("AK Automation", "AK Automation Log", "AK Automation Settings"):
		return

	# Recursion guard
	flag_key = f"ak_automation_running_{doc.doctype}_{doc.name}"
	if frappe.flags.get(flag_key):
		return

	trigger_type = EVENT_MAP.get(method)
	if not trigger_type:
		return

	# For after_insert, match both "On Create" and "On Update (includes Create)"
	trigger_types = [trigger_type]
	if method == "after_insert":
		trigger_types.append("On Update (includes Create)")

	for tt in trigger_types:
		automations = get_active_automations(doc.doctype, tt)
		for automation in automations:
			try:
				frappe.flags[flag_key] = True
				_run_automation(automation, doc, tt)
			except Exception as e:
				_log_execution(automation, doc, tt, "Failed", error=traceback.format_exc())
				# Update automation error stats
				frappe.db.set_value("AK Automation", automation.name, {
					"last_error": str(e)[:500],
				}, update_modified=False)
			finally:
				frappe.flags.pop(flag_key, None)


def _run_automation(automation, doc, trigger_type):
	"""Evaluate conditions and execute actions for a single automation."""
	start_time = time.time()

	# Check trigger_field for "On Update" — only fire if that field changed
	if (
		trigger_type == "On Update (includes Create)"
		and automation.trigger_field
		and hasattr(doc, "_doc_before_save")
		and doc._doc_before_save
	):
		old_val = doc._doc_before_save.get(automation.trigger_field)
		new_val = doc.get(automation.trigger_field)
		if old_val == new_val:
			return

	# Check "Only First Time" recurrence
	if automation.recurrence == "Only First Time Conditions Are Met":
		already_ran = frappe.db.exists("AK Automation Log", {
			"automation": automation.name,
			"reference_doctype": doc.doctype,
			"reference_name": doc.name,
			"status": "Success",
		})
		if already_ran:
			return

	# Evaluate conditions
	if not evaluate_conditions(automation, doc):
		_log_execution(automation, doc, trigger_type, "Skipped")
		return

	# Execute actions
	action_results = []
	from frappe_ak.dispatcher.actions import execute_action

	for action_row in automation.actions:
		if not action_row.enabled:
			continue
		try:
			result = execute_action(action_row, doc, automation)
			action_results.append({
				"action_type": action_row.action_type,
				"label": action_row.action_label or action_row.action_type,
				"status": "Success",
				"result": str(result)[:200] if result else None,
			})
		except Exception as e:
			action_results.append({
				"action_type": action_row.action_type,
				"label": action_row.action_label or action_row.action_type,
				"status": "Failed",
				"error": str(e)[:200],
			})
			raise

	elapsed_ms = (time.time() - start_time) * 1000

	_log_execution(
		automation, doc, trigger_type, "Success",
		actions_executed=action_results, elapsed_ms=elapsed_ms,
	)

	# Update stats
	frappe.db.set_value("AK Automation", automation.name, {
		"last_executed": frappe.utils.now_datetime(),
		"execution_count": (automation.execution_count or 0) + 1,
		"last_error": "",
	}, update_modified=False)


def get_active_automations(doctype, trigger_type):
	"""Fetch active automations for a DocType and trigger type, with Redis caching."""
	cache_key = f"ak_automations:{doctype}:{trigger_type}"
	cached = frappe.cache.get_value(cache_key)
	if cached is not None:
		# cached is a list of automation names
		return [frappe.get_doc("AK Automation", name) for name in cached]

	automation_names = frappe.get_all("AK Automation",
		filters={
			"reference_doctype": doctype,
			"trigger_type": trigger_type,
			"enabled": 1,
		},
		pluck="name",
	)
	frappe.cache.set_value(cache_key, automation_names, expires_in_sec=300)
	return [frappe.get_doc("AK Automation", name) for name in automation_names]


def run_cron_automations():
	"""Called every minute by scheduler. Runs Time Interval automations whose cron matches."""
	from croniter import croniter

	now = frappe.utils.now_datetime()

	automations = frappe.get_all("AK Automation",
		filters={
			"trigger_type": "Time Interval",
			"enabled": 1,
			"cron_expression": ["is", "set"],
		},
		pluck="name",
	)

	for auto_name in automations:
		automation = frappe.get_doc("AK Automation", auto_name)
		try:
			cron = croniter(automation.cron_expression, now)
			prev = cron.get_prev(float)
			# If the previous fire time is within the last 60 seconds, run it
			if (now.timestamp() - prev) < 60:
				# Cron automations run against all matching documents
				_run_cron_automation(automation)
		except Exception:
			frappe.log_error(
				title=f"AK Automation cron error: {auto_name}",
				message=traceback.format_exc()
			)


def _run_cron_automation(automation):
	"""Execute a cron-triggered automation against matching documents."""
	from frappe_ak.dispatcher.actions import execute_action

	# Build filters from conditions
	filters = {"doctype": automation.reference_doctype}
	docs = frappe.get_all(
		automation.reference_doctype,
		limit=100,
		pluck="name",
	)

	for doc_name in docs:
		doc = frappe.get_doc(automation.reference_doctype, doc_name)
		if evaluate_conditions(automation, doc):
			for action_row in automation.actions:
				if action_row.enabled:
					execute_action(action_row, doc, automation)


def cleanup_old_logs():
	"""Daily cleanup of old AK Automation Log entries."""
	settings = frappe.get_single("AK Automation Settings")
	retention_days = settings.log_retention_days or 30

	cutoff = frappe.utils.add_days(frappe.utils.today(), -retention_days)
	old_logs = frappe.get_all("AK Automation Log",
		filters={"executed_at": ["<", cutoff]},
		pluck="name",
		limit=1000,
	)

	for log_name in old_logs:
		frappe.delete_doc("AK Automation Log", log_name, ignore_permissions=True)

	if old_logs:
		frappe.db.commit()


def _log_execution(automation, doc, trigger_type, status, actions_executed=None, elapsed_ms=0, error=None):
	"""Create an AK Automation Log entry."""
	settings = frappe.get_single("AK Automation Settings")
	if not settings.enable_logging:
		return

	import json

	log_doc = frappe.get_doc({
		"doctype": "AK Automation Log",
		"automation": automation.name,
		"reference_doctype": doc.doctype,
		"reference_name": doc.name,
		"trigger_type": trigger_type,
		"status": status,
		"actions_executed": json.dumps(actions_executed) if actions_executed else None,
		"error_traceback": error,
		"execution_time_ms": elapsed_ms,
	})
	log_doc.flags.ignore_links = True
	log_doc.insert(ignore_permissions=True)
