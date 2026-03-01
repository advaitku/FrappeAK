import json
import time
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests import UnitTestCase

from frappe_ak.dispatcher.engine import (
	EVENT_MAP,
	_log_execution,
	_run_automation,
	cleanup_old_logs,
	get_active_automations,
	handle_event,
)


class TestHandleEvent(UnitTestCase):
	"""Tests for the handle_event wildcard dispatcher."""

	def test_skips_ak_automation_doctype(self):
		"""AK Automation docs should not trigger automations (avoid loops)."""
		doc = frappe._dict({"doctype": "AK Automation", "name": "TEST-001"})
		with patch("frappe_ak.dispatcher.engine.get_active_automations") as mock_get:
			handle_event(doc, "on_update")
			mock_get.assert_not_called()

	def test_skips_ak_automation_log(self):
		doc = frappe._dict({"doctype": "AK Automation Log", "name": "LOG-001"})
		with patch("frappe_ak.dispatcher.engine.get_active_automations") as mock_get:
			handle_event(doc, "on_update")
			mock_get.assert_not_called()

	def test_skips_ak_automation_settings(self):
		doc = frappe._dict({"doctype": "AK Automation Settings", "name": "AK Automation Settings"})
		with patch("frappe_ak.dispatcher.engine.get_active_automations") as mock_get:
			handle_event(doc, "on_update")
			mock_get.assert_not_called()

	def test_recursion_guard_prevents_reentry(self):
		"""If the recursion flag is already set, handle_event should skip."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-001"})
		flag_key = f"ak_automation_running_ToDo_TODO-001"
		frappe.flags[flag_key] = True
		try:
			with patch("frappe_ak.dispatcher.engine.get_active_automations") as mock_get:
				handle_event(doc, "on_update")
				mock_get.assert_not_called()
		finally:
			frappe.flags.pop(flag_key, None)

	def test_unknown_method_returns_early(self):
		"""Methods not in EVENT_MAP should be ignored."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-001"})
		with patch("frappe_ak.dispatcher.engine.get_active_automations") as mock_get:
			handle_event(doc, "some_unknown_method")
			mock_get.assert_not_called()

	def test_event_map_on_update(self):
		"""on_update should map to 'On Update (includes Create)'."""
		self.assertEqual(EVENT_MAP.get("on_update"), "On Update (includes Create)")

	def test_event_map_after_insert(self):
		"""after_insert should map to 'On Create'."""
		self.assertEqual(EVENT_MAP.get("after_insert"), "On Create")

	def test_event_map_before_save(self):
		self.assertEqual(EVENT_MAP.get("before_save"), "On Update (includes Create)")

	def test_event_map_on_submit(self):
		self.assertEqual(EVENT_MAP.get("on_submit"), "On Update (includes Create)")

	def test_event_map_on_cancel(self):
		self.assertEqual(EVENT_MAP.get("on_cancel"), "On Update (includes Create)")

	def test_after_insert_triggers_both_create_and_update(self):
		"""after_insert should query both On Create and On Update (includes Create)."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-001"})
		call_args = []

		def mock_get(doctype, trigger_type):
			call_args.append(trigger_type)
			return []

		with patch("frappe_ak.dispatcher.engine.get_active_automations", side_effect=mock_get):
			handle_event(doc, "after_insert")

		self.assertIn("On Create", call_args)
		self.assertIn("On Update (includes Create)", call_args)

	def test_on_update_only_triggers_update(self):
		"""on_update should only query On Update (includes Create)."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-001"})
		call_args = []

		def mock_get(doctype, trigger_type):
			call_args.append(trigger_type)
			return []

		with patch("frappe_ak.dispatcher.engine.get_active_automations", side_effect=mock_get):
			handle_event(doc, "on_update")

		self.assertEqual(call_args, ["On Update (includes Create)"])

	def test_exception_in_automation_does_not_stop_others(self):
		"""If one automation throws, subsequent automations should still run."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-001"})

		auto1 = frappe._dict({"name": "AUTO-001", "execution_count": 0})
		auto2 = frappe._dict({"name": "AUTO-002", "execution_count": 0})

		call_log = []

		def mock_run(automation, d, tt):
			call_log.append(automation.name)
			if automation.name == "AUTO-001":
				raise Exception("boom")

		with (
			patch("frappe_ak.dispatcher.engine.get_active_automations", return_value=[auto1, auto2]),
			patch("frappe_ak.dispatcher.engine._run_automation", side_effect=mock_run),
			patch("frappe_ak.dispatcher.engine._log_execution"),
			patch("frappe.db.set_value"),
		):
			handle_event(doc, "on_update")

		self.assertEqual(call_log, ["AUTO-001", "AUTO-002"])

	def test_exception_logs_failure_and_updates_last_error(self):
		"""When an automation throws, it should log failure and update last_error."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-001"})
		auto = frappe._dict({"name": "AUTO-001", "execution_count": 0})

		with (
			patch("frappe_ak.dispatcher.engine.get_active_automations", return_value=[auto]),
			patch("frappe_ak.dispatcher.engine._run_automation", side_effect=Exception("test error")),
			patch("frappe_ak.dispatcher.engine._log_execution") as mock_log,
			patch("frappe.db.set_value") as mock_set,
		):
			handle_event(doc, "on_update")

		mock_log.assert_called_once()
		self.assertEqual(mock_log.call_args[0][3], "Failed")
		mock_set.assert_called_once()
		set_args = mock_set.call_args
		self.assertIn("last_error", set_args[0][2])

	def test_recursion_flag_cleared_after_execution(self):
		"""The recursion flag should be cleared even if _run_automation succeeds."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-CLEAR"})
		auto = frappe._dict({"name": "AUTO-001", "execution_count": 0})

		with (
			patch("frappe_ak.dispatcher.engine.get_active_automations", return_value=[auto]),
			patch("frappe_ak.dispatcher.engine._run_automation"),
		):
			handle_event(doc, "on_update")

		flag_key = "ak_automation_running_ToDo_TODO-CLEAR"
		self.assertIsNone(frappe.flags.get(flag_key))

	def test_recursion_flag_cleared_after_exception(self):
		"""The recursion flag should be cleared even if _run_automation throws."""
		doc = frappe._dict({"doctype": "ToDo", "name": "TODO-ERR"})
		auto = frappe._dict({"name": "AUTO-001", "execution_count": 0})

		with (
			patch("frappe_ak.dispatcher.engine.get_active_automations", return_value=[auto]),
			patch("frappe_ak.dispatcher.engine._run_automation", side_effect=Exception("boom")),
			patch("frappe_ak.dispatcher.engine._log_execution"),
			patch("frappe.db.set_value"),
		):
			handle_event(doc, "on_update")

		flag_key = "ak_automation_running_ToDo_TODO-ERR"
		self.assertIsNone(frappe.flags.get(flag_key))


class TestRunAutomation(UnitTestCase):
	"""Tests for _run_automation logic."""

	def _make_action(self, action_type="Update Fields", enabled=1):
		return frappe._dict({
			"action_type": action_type,
			"action_label": action_type,
			"enabled": enabled,
			"idx": 1,
		})

	def _make_automation(self, trigger_type="On Create", trigger_field=None, recurrence="Every Time", actions=None):
		return frappe._dict({
			"name": "AUTO-TEST",
			"title": "Test Automation",
			"trigger_type": trigger_type,
			"trigger_field": trigger_field,
			"recurrence": recurrence,
			"all_conditions": [],
			"any_conditions": [],
			"actions": actions or [self._make_action()],
			"execution_count": 0,
		})

	def test_trigger_field_unchanged_skips(self):
		"""If trigger_field is set and hasn't changed, skip the automation."""
		auto = self._make_automation(
			trigger_type="On Update (includes Create)",
			trigger_field="status",
		)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1", "status": "Open"})
		doc._doc_before_save = frappe._dict({"status": "Open"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions") as mock_eval,
			patch("frappe_ak.dispatcher.engine._log_execution"),
		):
			_run_automation(auto, doc, "On Update (includes Create)")
			mock_eval.assert_not_called()

	def test_trigger_field_changed_proceeds(self):
		"""If trigger_field has changed, automation should evaluate conditions."""
		auto = self._make_automation(
			trigger_type="On Update (includes Create)",
			trigger_field="status",
		)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1", "status": "Closed"})
		doc._doc_before_save = frappe._dict({"status": "Open"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=False),
			patch("frappe_ak.dispatcher.engine._log_execution"),
		):
			_run_automation(auto, doc, "On Update (includes Create)")

	def test_new_doc_no_before_save_passes_trigger_field(self):
		"""New documents have no _doc_before_save, so trigger_field check should pass."""
		auto = self._make_automation(
			trigger_type="On Update (includes Create)",
			trigger_field="status",
		)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1", "status": "Open"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=False),
			patch("frappe_ak.dispatcher.engine._log_execution"),
		):
			_run_automation(auto, doc, "On Update (includes Create)")

	def test_only_first_time_skips_second_run(self):
		"""'Only First Time Conditions Are Met' should skip if a prior Success log exists."""
		auto = self._make_automation(recurrence="Only First Time Conditions Are Met")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe_ak.dispatcher.engine.evaluate_conditions") as mock_eval,
			patch("frappe_ak.dispatcher.engine._log_execution"),
		):
			_run_automation(auto, doc, "On Create")
			mock_eval.assert_not_called()

	def test_every_time_always_runs(self):
		"""'Every Time' recurrence should not check for prior logs."""
		auto = self._make_automation(recurrence="Every Time")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		with (
			patch("frappe.db.exists") as mock_exists,
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=False),
			patch("frappe_ak.dispatcher.engine._log_execution"),
		):
			_run_automation(auto, doc, "On Create")
			mock_exists.assert_not_called()

	def test_conditions_fail_logs_skipped(self):
		"""When conditions fail, should log as 'Skipped'."""
		auto = self._make_automation()
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=False),
			patch("frappe_ak.dispatcher.engine._log_execution") as mock_log,
		):
			_run_automation(auto, doc, "On Create")
			mock_log.assert_called_once()
			self.assertEqual(mock_log.call_args[0][3], "Skipped")

	def test_conditions_pass_executes_actions(self):
		"""When conditions pass, actions should be executed and logged as Success."""
		auto = self._make_automation()
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=True),
			patch("frappe_ak.dispatcher.actions.execute_action", return_value="done"),
			patch("frappe_ak.dispatcher.engine._log_execution") as mock_log,
			patch("frappe.db.set_value"),
		):
			_run_automation(auto, doc, "On Create")
			mock_log.assert_called_once()
			self.assertEqual(mock_log.call_args[0][3], "Success")

	def test_disabled_actions_skipped(self):
		"""Disabled actions should not be executed."""
		actions = [
			self._make_action(enabled=0),
			self._make_action(action_type="Create Todo", enabled=1),
		]
		auto = self._make_automation(actions=actions)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		executed = []

		def mock_execute(action_row, d, a):
			executed.append(action_row.action_type)
			return "done"

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=True),
			patch("frappe_ak.dispatcher.actions.execute_action", side_effect=mock_execute),
			patch("frappe_ak.dispatcher.engine._log_execution"),
			patch("frappe.db.set_value"),
		):
			_run_automation(auto, doc, "On Create")

		self.assertEqual(executed, ["Create Todo"])

	def test_action_failure_raises_and_records(self):
		"""If an action throws, the error should propagate."""
		auto = self._make_automation()
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=True),
			patch("frappe_ak.dispatcher.actions.execute_action", side_effect=Exception("action failed")),
		):
			with self.assertRaises(Exception):
				_run_automation(auto, doc, "On Create")

	def test_execution_stats_updated_on_success(self):
		"""On success, last_executed, execution_count, last_error should be updated."""
		auto = self._make_automation()
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=True),
			patch("frappe_ak.dispatcher.actions.execute_action", return_value="done"),
			patch("frappe_ak.dispatcher.engine._log_execution"),
			patch("frappe.db.set_value") as mock_set,
		):
			_run_automation(auto, doc, "On Create")
			mock_set.assert_called_once()
			update_dict = mock_set.call_args[0][2]
			self.assertIn("last_executed", update_dict)
			self.assertEqual(update_dict["execution_count"], 1)
			self.assertEqual(update_dict["last_error"], "")

	def test_action_results_recorded(self):
		"""Action results should be passed to _log_execution."""
		auto = self._make_automation()
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})

		with (
			patch("frappe_ak.dispatcher.engine.evaluate_conditions", return_value=True),
			patch("frappe_ak.dispatcher.actions.execute_action", return_value="Updated fields: status"),
			patch("frappe_ak.dispatcher.engine._log_execution") as mock_log,
			patch("frappe.db.set_value"),
		):
			_run_automation(auto, doc, "On Create")
			call_kwargs = mock_log.call_args[1]
			actions = call_kwargs.get("actions_executed", [])
			self.assertEqual(len(actions), 1)
			self.assertEqual(actions[0]["status"], "Success")
			self.assertIn("Updated fields", actions[0]["result"])


class TestGetActiveAutomations(UnitTestCase):
	"""Tests for the cached automation lookup."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Clear cache before tests
		frappe.cache.delete_keys("ak_automations:*")

		cls.test_automation = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Test Active Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 1,
			"actions": [{
				"action_type": "Update Fields",
				"action_label": "Test",
				"enabled": 1,
			}],
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Automation", cls.test_automation.name, ignore_permissions=True, force=True)
		frappe.cache.delete_keys("ak_automations:*")
		frappe.db.commit()
		super().tearDownClass()

	def setUp(self):
		frappe.cache.delete_keys("ak_automations:*")

	def test_returns_matching_automations(self):
		result = get_active_automations("ToDo", "On Create")
		names = [a.name for a in result]
		self.assertIn(self.test_automation.name, names)

	def test_does_not_return_wrong_trigger(self):
		result = get_active_automations("ToDo", "Time Interval")
		names = [a.name for a in result]
		self.assertNotIn(self.test_automation.name, names)

	def test_does_not_return_wrong_doctype(self):
		result = get_active_automations("Event", "On Create")
		names = [a.name for a in result]
		self.assertNotIn(self.test_automation.name, names)

	def test_caching_returns_same_results(self):
		"""Second call should use cache and return same automations."""
		result1 = get_active_automations("ToDo", "On Create")
		result2 = get_active_automations("ToDo", "On Create")
		self.assertEqual(
			[a.name for a in result1],
			[a.name for a in result2],
		)

	def test_cache_invalidation(self):
		"""After clearing cache, fresh results should be returned."""
		get_active_automations("ToDo", "On Create")
		frappe.cache.delete_keys("ak_automations:*")
		# Should not raise — falls back to DB
		result = get_active_automations("ToDo", "On Create")
		self.assertIsInstance(result, list)


class TestCleanupOldLogs(UnitTestCase):
	"""Tests for the daily log cleanup."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.test_automation = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Cleanup Test Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 0,
			"actions": [{
				"action_type": "Update Fields",
				"action_label": "Test",
				"enabled": 1,
			}],
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Automation", cls.test_automation.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_deletes_old_logs(self):
		"""Logs older than retention_days should be deleted."""
		old_date = frappe.utils.add_days(frappe.utils.today(), -60)
		log = frappe.get_doc({
			"doctype": "AK Automation Log",
			"automation": self.test_automation.name,
			"reference_doctype": "ToDo",
			"reference_name": "test",
			"trigger_type": "On Create",
			"status": "Success",
			"executed_at": old_date,
			"execution_time_ms": 1.0,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({
				"log_retention_days": 30,
			})
			cleanup_old_logs()

		self.assertFalse(frappe.db.exists("AK Automation Log", log.name))

	def test_keeps_recent_logs(self):
		"""Logs newer than retention_days should be kept."""
		log = frappe.get_doc({
			"doctype": "AK Automation Log",
			"automation": self.test_automation.name,
			"reference_doctype": "ToDo",
			"reference_name": "test",
			"trigger_type": "On Create",
			"status": "Success",
			"executed_at": frappe.utils.now_datetime(),
			"execution_time_ms": 1.0,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({
				"log_retention_days": 30,
			})
			cleanup_old_logs()

		self.assertTrue(frappe.db.exists("AK Automation Log", log.name))
		frappe.delete_doc("AK Automation Log", log.name, ignore_permissions=True, force=True)


class TestLogExecution(UnitTestCase):
	"""Tests for _log_execution."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.test_automation = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Log Test Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 0,
			"actions": [{
				"action_type": "Update Fields",
				"action_label": "Test",
				"enabled": 1,
			}],
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		# Clean up any logs
		logs = frappe.get_all("AK Automation Log",
			filters={"automation": cls.test_automation.name},
			pluck="name",
		)
		for log_name in logs:
			frappe.delete_doc("AK Automation Log", log_name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Automation", cls.test_automation.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_creates_log_when_enabled(self):
		doc = frappe._dict({"doctype": "ToDo", "name": "T-LOG"})
		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({"enable_logging": 1})
			_log_execution(self.test_automation, doc, "On Create", "Success", elapsed_ms=42.5)

		logs = frappe.get_all("AK Automation Log",
			filters={"automation": self.test_automation.name, "reference_name": "T-LOG"},
			pluck="name",
		)
		self.assertTrue(len(logs) > 0)
		for log_name in logs:
			frappe.delete_doc("AK Automation Log", log_name, ignore_permissions=True, force=True)

	def test_skips_when_logging_disabled(self):
		doc = frappe._dict({"doctype": "ToDo", "name": "T-NOLOG"})
		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({"enable_logging": 0})
			_log_execution(self.test_automation, doc, "On Create", "Success")

		logs = frappe.get_all("AK Automation Log",
			filters={"automation": self.test_automation.name, "reference_name": "T-NOLOG"},
			pluck="name",
		)
		self.assertEqual(len(logs), 0)

	def test_actions_json_serialized(self):
		doc = frappe._dict({"doctype": "ToDo", "name": "T-JSON"})
		actions = [{"action_type": "Update Fields", "status": "Success", "result": "ok"}]
		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({"enable_logging": 1})
			_log_execution(self.test_automation, doc, "On Create", "Success", actions_executed=actions)

		logs = frappe.get_all("AK Automation Log",
			filters={"automation": self.test_automation.name, "reference_name": "T-JSON"},
			fields=["name", "actions_executed"],
		)
		self.assertTrue(len(logs) > 0)
		parsed = json.loads(logs[0].actions_executed)
		self.assertEqual(parsed[0]["action_type"], "Update Fields")

		for log in logs:
			frappe.delete_doc("AK Automation Log", log.name, ignore_permissions=True, force=True)

	def test_error_traceback_stored(self):
		doc = frappe._dict({"doctype": "ToDo", "name": "T-ERR"})
		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({"enable_logging": 1})
			_log_execution(
				self.test_automation, doc, "On Create", "Failed",
				error="Traceback (most recent call last):\nValueError: test",
			)

		logs = frappe.get_all("AK Automation Log",
			filters={"automation": self.test_automation.name, "reference_name": "T-ERR"},
			fields=["name", "error_traceback", "status"],
		)
		self.assertTrue(len(logs) > 0)
		self.assertEqual(logs[0].status, "Failed")
		self.assertIn("ValueError", logs[0].error_traceback)

		for log in logs:
			frappe.delete_doc("AK Automation Log", log.name, ignore_permissions=True, force=True)


class TestCronAutomations(UnitTestCase):
	"""Tests for cron automation scheduling."""

	def test_run_cron_automations_skips_non_matching(self):
		"""Cron that doesn't match current time should not execute."""
		with (
			patch("frappe.get_all", return_value=["AUTO-CRON"]),
			patch("frappe.get_doc") as mock_getdoc,
			patch("frappe_ak.dispatcher.engine._run_cron_automation") as mock_run,
		):
			# Set up a cron expression that won't match (Feb 30 doesn't exist)
			mock_auto = frappe._dict({
				"name": "AUTO-CRON",
				"cron_expression": "0 0 30 2 *",
			})
			mock_getdoc.return_value = mock_auto

			from frappe_ak.dispatcher.engine import run_cron_automations
			# The croniter will compute prev fire time far in the past
			run_cron_automations()
			mock_run.assert_not_called()

	def test_invalid_cron_expression_logged(self):
		"""Invalid cron expressions should be logged, not crash."""
		with (
			patch("frappe.get_all", return_value=["AUTO-BAD"]),
			patch("frappe.get_doc") as mock_getdoc,
			patch("frappe.log_error") as mock_log_err,
		):
			mock_auto = frappe._dict({
				"name": "AUTO-BAD",
				"cron_expression": "invalid cron",
			})
			mock_getdoc.return_value = mock_auto

			from frappe_ak.dispatcher.engine import run_cron_automations
			run_cron_automations()
			mock_log_err.assert_called()
