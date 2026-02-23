from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from frappe_ak.dispatcher.conditions import (
	evaluate_conditions,
	_eval_text,
	_eval_numeric,
	_eval_date,
	_eval_change,
)
from frappe_ak.dispatcher.formula import (
	resolve_value,
	evaluate_expression,
	_fn_concat,
	_fn_uppercase,
	_fn_lowercase,
	_fn_trim,
	_fn_round,
	_fn_abs,
)


class TestConditions(UnitTestCase):
	"""Unit tests for condition evaluation logic."""

	# ── Text operators ──

	def test_text_is(self):
		self.assertTrue(_eval_text("is", "Open", "Open"))
		self.assertFalse(_eval_text("is", "Open", "Closed"))

	def test_text_is_not(self):
		self.assertTrue(_eval_text("is not", "Open", "Closed"))
		self.assertFalse(_eval_text("is not", "Open", "Open"))

	def test_text_contains(self):
		self.assertTrue(_eval_text("contains", "Hello World", "world"))
		self.assertFalse(_eval_text("contains", "Hello World", "xyz"))

	def test_text_does_not_contain(self):
		self.assertTrue(_eval_text("does not contain", "Hello World", "xyz"))
		self.assertFalse(_eval_text("does not contain", "Hello World", "world"))

	def test_text_starts_with(self):
		self.assertTrue(_eval_text("starts with", "Hello World", "hello"))
		self.assertFalse(_eval_text("starts with", "Hello World", "world"))

	def test_text_ends_with(self):
		self.assertTrue(_eval_text("ends with", "Hello World", "world"))
		self.assertFalse(_eval_text("ends with", "Hello World", "hello"))

	def test_text_empty_values(self):
		self.assertTrue(_eval_text("is", "", ""))
		self.assertTrue(_eval_text("is", None, ""))
		self.assertFalse(_eval_text("contains", "", "something"))

	# ── Numeric operators ──

	def test_numeric_equal(self):
		self.assertTrue(_eval_numeric("=", 100, "100", None))
		self.assertFalse(_eval_numeric("=", 100, "200", None))

	def test_numeric_not_equal(self):
		self.assertTrue(_eval_numeric("!=", 100, "200", None))
		self.assertFalse(_eval_numeric("!=", 100, "100", None))

	def test_numeric_greater(self):
		self.assertTrue(_eval_numeric(">", 200, "100", None))
		self.assertFalse(_eval_numeric(">", 50, "100", None))

	def test_numeric_less(self):
		self.assertTrue(_eval_numeric("<", 50, "100", None))
		self.assertFalse(_eval_numeric("<", 200, "100", None))

	def test_numeric_between(self):
		self.assertTrue(_eval_numeric("between", 50, "10", "100"))
		self.assertFalse(_eval_numeric("between", 200, "10", "100"))

	def test_numeric_boundary(self):
		self.assertTrue(_eval_numeric(">=", 100, "100", None))
		self.assertTrue(_eval_numeric("<=", 100, "100", None))

	# ── Date operators ──

	def test_date_is_today(self):
		from frappe.utils import today
		self.assertTrue(_eval_date("is today", today(), None, None))
		self.assertFalse(_eval_date("is today", "2020-01-01", None, None))

	def test_date_is_tomorrow(self):
		from frappe.utils import add_days, today
		tomorrow = add_days(today(), 1)
		self.assertTrue(_eval_date("is tomorrow", tomorrow, None, None))
		self.assertFalse(_eval_date("is tomorrow", today(), None, None))

	def test_date_is_yesterday(self):
		from frappe.utils import add_days, today
		yesterday = add_days(today(), -1)
		self.assertTrue(_eval_date("is yesterday", yesterday, None, None))
		self.assertFalse(_eval_date("is yesterday", today(), None, None))

	def test_date_before(self):
		self.assertTrue(_eval_date("before", "2024-01-01", "2024-06-01", None))
		self.assertFalse(_eval_date("before", "2024-06-01", "2024-01-01", None))

	def test_date_after(self):
		self.assertTrue(_eval_date("after", "2024-06-01", "2024-01-01", None))
		self.assertFalse(_eval_date("after", "2024-01-01", "2024-06-01", None))

	def test_date_between(self):
		self.assertTrue(_eval_date("between", "2024-03-15", "2024-01-01", "2024-06-01"))
		self.assertFalse(_eval_date("between", "2024-09-15", "2024-01-01", "2024-06-01"))

	def test_date_empty_value(self):
		self.assertFalse(_eval_date("is today", None, None, None))

	# ── Change operators ──

	def test_has_changed_new_doc(self):
		"""New documents (no _doc_before_save) should count as 'has changed'."""
		doc = frappe._dict({"status": "Open"})
		self.assertTrue(_eval_change("has changed", "status", None, doc))

	def test_has_changed_to_new_doc(self):
		doc = frappe._dict({"status": "Open"})
		self.assertTrue(_eval_change("has changed to", "status", "Open", doc))
		self.assertFalse(_eval_change("has changed to", "status", "Closed", doc))

	def test_has_changed_with_before_save(self):
		doc = frappe._dict({"status": "Closed"})
		doc._doc_before_save = frappe._dict({"status": "Open"})
		self.assertTrue(_eval_change("has changed", "status", None, doc))

	def test_has_not_changed(self):
		doc = frappe._dict({"status": "Open"})
		doc._doc_before_save = frappe._dict({"status": "Open"})
		self.assertFalse(_eval_change("has changed", "status", None, doc))

	def test_has_changed_to(self):
		doc = frappe._dict({"status": "Closed"})
		doc._doc_before_save = frappe._dict({"status": "Open"})
		self.assertTrue(_eval_change("has changed to", "status", "Closed", doc))
		self.assertFalse(_eval_change("has changed to", "status", "Open", doc))

	def test_has_changed_from(self):
		doc = frappe._dict({"status": "Closed"})
		doc._doc_before_save = frappe._dict({"status": "Open"})
		self.assertTrue(_eval_change("has changed from", "status", "Open", doc))
		self.assertFalse(_eval_change("has changed from", "status", "Closed", doc))


class TestFormulas(UnitTestCase):
	"""Unit tests for formula/expression evaluation."""

	# ── Built-in functions ──

	def test_concat(self):
		self.assertEqual(_fn_concat("Hello", " ", "World"), "Hello World")
		self.assertEqual(_fn_concat("A", None, "B"), "AB")

	def test_uppercase(self):
		self.assertEqual(_fn_uppercase("hello"), "HELLO")
		self.assertEqual(_fn_uppercase(None), "")

	def test_lowercase(self):
		self.assertEqual(_fn_lowercase("HELLO"), "hello")

	def test_trim(self):
		self.assertEqual(_fn_trim("  hello  "), "hello")

	def test_round(self):
		self.assertEqual(_fn_round(3.14159, 2), 3.14)
		self.assertEqual(_fn_round(3.5, 0), 4)

	def test_abs(self):
		self.assertEqual(_fn_abs(-42), 42)
		self.assertEqual(_fn_abs(42), 42)

	# ── resolve_value ──

	def test_resolve_static_value(self):
		doc = frappe._dict({"name": "TEST"})
		result = resolve_value("Static Value", {"value": "hello"}, doc)
		self.assertEqual(result, "hello")

	def test_resolve_today(self):
		from frappe.utils import today
		doc = frappe._dict({})
		result = resolve_value("Today", {}, doc)
		self.assertEqual(result, today())

	def test_resolve_today_plus_n(self):
		from frappe.utils import today, add_days
		doc = frappe._dict({})
		result = resolve_value("Today + N Days", {"days_offset": 7}, doc)
		self.assertEqual(result, add_days(today(), 7))

	def test_resolve_today_minus_n(self):
		from frappe.utils import today, add_days
		doc = frappe._dict({})
		result = resolve_value("Today - N Days", {"days_offset": 3}, doc)
		self.assertEqual(result, add_days(today(), -3))

	def test_resolve_use_field(self):
		doc = frappe._dict({"first_name": "Alice", "last_name": "Smith"})
		result = resolve_value("Use Field", {"source_field": "first_name"}, doc)
		self.assertEqual(result, "Alice")

	def test_resolve_current_user(self):
		doc = frappe._dict({})
		result = resolve_value("Current User", {}, doc)
		self.assertEqual(result, frappe.session.user)

	def test_resolve_clear(self):
		doc = frappe._dict({})
		result = resolve_value("Clear", {}, doc)
		self.assertIsNone(result)


class TestEvaluateConditions(UnitTestCase):
	"""Test the top-level evaluate_conditions function with mock automations."""

	def _make_automation(self, all_conds=None, any_conds=None):
		auto = frappe._dict({
			"all_conditions": all_conds or [],
			"any_conditions": any_conds or [],
		})
		return auto

	def _make_cond(self, field, operator, value, value2=None):
		return frappe._dict({
			"field": field,
			"operator": operator,
			"value": value,
			"value2": value2,
		})

	def test_no_conditions_returns_true(self):
		auto = self._make_automation()
		doc = frappe._dict({"doctype": "ToDo", "status": "Open"})
		self.assertTrue(evaluate_conditions(auto, doc))

	def test_all_conditions_pass(self):
		conds = [
			self._make_cond("status", "is", "Open"),
		]
		auto = self._make_automation(all_conds=conds)
		doc = frappe._dict({"doctype": "ToDo", "status": "Open"})
		self.assertTrue(evaluate_conditions(auto, doc))

	def test_all_conditions_fail(self):
		conds = [
			self._make_cond("status", "is", "Open"),
			self._make_cond("priority", "is", "High"),
		]
		auto = self._make_automation(all_conds=conds)
		doc = frappe._dict({"doctype": "ToDo", "status": "Open", "priority": "Low"})
		self.assertFalse(evaluate_conditions(auto, doc))

	def test_any_conditions_one_passes(self):
		any_conds = [
			self._make_cond("status", "is", "Open"),
			self._make_cond("status", "is", "Closed"),
		]
		auto = self._make_automation(any_conds=any_conds)
		doc = frappe._dict({"doctype": "ToDo", "status": "Open"})
		self.assertTrue(evaluate_conditions(auto, doc))

	def test_any_conditions_none_pass(self):
		any_conds = [
			self._make_cond("status", "is", "Closed"),
			self._make_cond("status", "is", "Cancelled"),
		]
		auto = self._make_automation(any_conds=any_conds)
		doc = frappe._dict({"doctype": "ToDo", "status": "Open"})
		self.assertFalse(evaluate_conditions(auto, doc))

	def test_combined_all_and_any(self):
		all_conds = [self._make_cond("priority", "is", "High")]
		any_conds = [
			self._make_cond("status", "is", "Open"),
			self._make_cond("status", "is", "Pending"),
		]
		auto = self._make_automation(all_conds=all_conds, any_conds=any_conds)

		# Both match
		doc = frappe._dict({"doctype": "ToDo", "priority": "High", "status": "Open"})
		self.assertTrue(evaluate_conditions(auto, doc))

		# All passes, any fails
		doc2 = frappe._dict({"doctype": "ToDo", "priority": "High", "status": "Closed"})
		self.assertFalse(evaluate_conditions(auto, doc2))

		# All fails
		doc3 = frappe._dict({"doctype": "ToDo", "priority": "Low", "status": "Open"})
		self.assertFalse(evaluate_conditions(auto, doc3))


class TestAKAutomationController(UnitTestCase):
	"""Tests for AK Automation DocType controller methods."""

	def test_validate_throws_without_actions(self):
		"""Automation without actions should fail validation."""
		auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "No Actions Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 1,
			"actions": [],
		})
		with self.assertRaises(Exception):
			auto.insert(ignore_permissions=True)

	def test_validate_passes_with_action(self):
		"""Automation with at least one action should pass validation."""
		auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Valid Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 1,
			"actions": [{
				"action_type": "Run Script",
				"action_label": "Test",
				"enabled": 1,
				"script_code": "1",
			}],
		})
		auto.insert(ignore_permissions=True)
		self.assertTrue(auto.name)
		frappe.delete_doc("AK Automation", auto.name, ignore_permissions=True, force=True)

	def test_cache_cleared_on_update(self):
		"""Cache should be cleared when automation is updated."""
		auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Cache Test Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 1,
			"actions": [{
				"action_type": "Run Script",
				"action_label": "Test",
				"enabled": 1,
				"script_code": "1",
			}],
		}).insert(ignore_permissions=True)

		with patch.object(frappe.cache(), "delete_keys") as mock_delete:
			auto.title = "Updated Title"
			auto.save(ignore_permissions=True)
			mock_delete.assert_called()

		frappe.delete_doc("AK Automation", auto.name, ignore_permissions=True, force=True)

	def test_cache_cleared_on_trash(self):
		"""Cache should be cleared when automation is deleted."""
		auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Trash Cache Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 1,
			"actions": [{
				"action_type": "Run Script",
				"action_label": "Test",
				"enabled": 1,
				"script_code": "1",
			}],
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		with patch.object(frappe.cache(), "delete_keys") as mock_delete:
			frappe.delete_doc("AK Automation", auto.name, ignore_permissions=True, force=True)
			mock_delete.assert_called()

	def test_creation_with_all_fields(self):
		"""Automation with all field types should be created successfully."""
		auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Full Fields Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "On Update (includes Create)",
			"trigger_field": "status",
			"enabled": 1,
			"recurrence": "Only First Time Conditions Are Met",
			"description": "Test automation with all fields",
			"all_conditions": [{
				"field": "status",
				"operator": "is",
				"value": "Open",
			}],
			"any_conditions": [{
				"field": "priority",
				"operator": "is",
				"value": "High",
			}],
			"actions": [{
				"action_type": "Update Fields",
				"action_label": "Update status",
				"enabled": 1,
			}],
		}).insert(ignore_permissions=True)

		self.assertTrue(auto.name)
		self.assertEqual(auto.trigger_type, "On Update (includes Create)")
		self.assertEqual(auto.trigger_field, "status")
		self.assertEqual(auto.recurrence, "Only First Time Conditions Are Met")
		self.assertEqual(len(auto.all_conditions), 1)
		self.assertEqual(len(auto.any_conditions), 1)
		self.assertEqual(len(auto.actions), 1)

		frappe.delete_doc("AK Automation", auto.name, ignore_permissions=True, force=True)
