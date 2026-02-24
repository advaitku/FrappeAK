"""Extended condition tests — covers _evaluate_single routing, date edge cases, numeric edge cases."""

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import today, add_days, getdate

from frappe_ak.dispatcher.conditions import (
	_eval_date,
	_eval_numeric,
	_eval_text,
	_eval_change,
	_evaluate_single,
	evaluate_conditions,
)


class TestEvaluateSingle(UnitTestCase):
	"""Tests for _evaluate_single condition dispatcher."""

	def _make_cond(self, field, operator, value, value2=None):
		return frappe._dict({
			"field": field,
			"operator": operator,
			"value": value,
			"value2": value2,
		})

	def test_change_operators_bypass_fieldtype(self):
		"""Change operators should work regardless of field type."""
		cond = self._make_cond("status", "has changed", None)
		doc = frappe._dict({"doctype": "ToDo", "status": "Closed"})
		doc._doc_before_save = frappe._dict({"status": "Open"})
		self.assertTrue(_evaluate_single(cond, doc))

	def test_is_empty_truthy(self):
		"""'is empty' should return True for falsy values."""
		cond = self._make_cond("description", "is empty", None)
		doc = frappe._dict({"doctype": "ToDo", "description": ""})
		self.assertTrue(_evaluate_single(cond, doc))

	def test_is_empty_none(self):
		cond = self._make_cond("description", "is empty", None)
		doc = frappe._dict({"doctype": "ToDo", "description": None})
		self.assertTrue(_evaluate_single(cond, doc))

	def test_is_not_empty(self):
		cond = self._make_cond("description", "is not empty", None)
		doc = frappe._dict({"doctype": "ToDo", "description": "hello"})
		self.assertTrue(_evaluate_single(cond, doc))

	def test_is_not_empty_false(self):
		cond = self._make_cond("description", "is not empty", None)
		doc = frappe._dict({"doctype": "ToDo", "description": ""})
		self.assertFalse(_evaluate_single(cond, doc))

	def test_unknown_field_defaults_to_data(self):
		"""Fields not found in meta should default to Data (text) operators."""
		cond = self._make_cond("nonexistent_field_xyz", "is", "test")
		doc = frappe._dict({"doctype": "ToDo", "nonexistent_field_xyz": "test"})
		# Should not crash — defaults to Data fieldtype and uses text eval
		result = _evaluate_single(cond, doc)
		self.assertTrue(result)


class TestDateEdgeCases(UnitTestCase):
	"""Edge case tests for date condition evaluation."""

	def test_less_than_days_ago_boundary(self):
		"""'less than days ago' with exact boundary — cutoff date should NOT match."""
		exactly_5_days_ago = add_days(today(), -5)
		# "less than 5 days ago" means doc_date > (today - 5)
		# Exact boundary should be False (not strictly greater)
		self.assertFalse(_eval_date("less than days ago", exactly_5_days_ago, "5", None))

	def test_less_than_days_ago_within(self):
		"""Date within the 'less than days ago' window should match."""
		two_days_ago = add_days(today(), -2)
		self.assertTrue(_eval_date("less than days ago", two_days_ago, "5", None))

	def test_less_than_days_ago_outside(self):
		"""Date outside the 'less than days ago' window should not match."""
		ten_days_ago = add_days(today(), -10)
		self.assertFalse(_eval_date("less than days ago", ten_days_ago, "5", None))

	def test_more_than_days_ago_boundary(self):
		"""'more than days ago' with exact boundary."""
		exactly_5_days_ago = add_days(today(), -5)
		# "more than 5 days ago" means doc_date < (today - 5)
		self.assertFalse(_eval_date("more than days ago", exactly_5_days_ago, "5", None))

	def test_more_than_days_ago_match(self):
		ten_days_ago = add_days(today(), -10)
		self.assertTrue(_eval_date("more than days ago", ten_days_ago, "5", None))

	def test_less_than_days_later_includes_today(self):
		"""'less than days later' should include today."""
		self.assertTrue(_eval_date("less than days later", today(), "5", None))

	def test_less_than_days_later_excludes_past(self):
		"""'less than days later' should exclude past dates."""
		yesterday = add_days(today(), -1)
		self.assertFalse(_eval_date("less than days later", yesterday, "5", None))

	def test_less_than_days_later_within(self):
		two_days_later = add_days(today(), 2)
		self.assertTrue(_eval_date("less than days later", two_days_later, "5", None))

	def test_less_than_days_later_boundary(self):
		"""Exact boundary should be excluded (strictly less than)."""
		exactly_5_later = add_days(today(), 5)
		self.assertFalse(_eval_date("less than days later", exactly_5_later, "5", None))

	def test_more_than_days_later_match(self):
		ten_days_later = add_days(today(), 10)
		self.assertTrue(_eval_date("more than days later", ten_days_later, "5", None))

	def test_more_than_days_later_excludes_today(self):
		self.assertFalse(_eval_date("more than days later", today(), "5", None))

	def test_invalid_date_returns_false(self):
		"""Invalid date string should return False, not crash."""
		self.assertFalse(_eval_date("is today", "not-a-date", None, None))

	def test_date_is_equality(self):
		self.assertTrue(_eval_date("is", "2024-06-15", "2024-06-15", None))
		self.assertFalse(_eval_date("is", "2024-06-15", "2024-06-16", None))

	def test_date_is_not(self):
		self.assertTrue(_eval_date("is not", "2024-06-15", "2024-06-16", None))
		self.assertFalse(_eval_date("is not", "2024-06-15", "2024-06-15", None))

	def test_date_empty_returns_true_for_is_empty(self):
		self.assertTrue(_eval_date("is empty", None, None, None))

	def test_date_empty_returns_false_for_other_ops(self):
		self.assertFalse(_eval_date("before", None, "2024-01-01", None))
		self.assertFalse(_eval_date("after", None, "2024-01-01", None))


class TestNumericEdgeCases(UnitTestCase):
	"""Edge case tests for numeric condition evaluation."""

	def test_non_numeric_string_becomes_zero(self):
		"""Non-numeric strings should be converted to 0.0 via flt()."""
		self.assertTrue(_eval_numeric("=", "abc", "0", None))

	def test_none_value_becomes_zero(self):
		self.assertTrue(_eval_numeric("=", None, "0", None))

	def test_float_precision(self):
		"""Float comparisons should work via flt() conversion."""
		# flt() rounds both sides, so standard float values work
		self.assertTrue(_eval_numeric("=", 10.5, "10.5", None))

	def test_negative_numbers(self):
		self.assertTrue(_eval_numeric("<", -5, "0", None))
		self.assertTrue(_eval_numeric(">", 0, "-5", None))

	def test_between_inclusive(self):
		"""Between should be inclusive on both ends."""
		self.assertTrue(_eval_numeric("between", 10, "10", "20"))
		self.assertTrue(_eval_numeric("between", 20, "10", "20"))
		self.assertFalse(_eval_numeric("between", 9.99, "10", "20"))
		self.assertFalse(_eval_numeric("between", 20.01, "10", "20"))

	def test_unknown_operator_returns_false(self):
		self.assertFalse(_eval_numeric("unknown_op", 10, "10", None))


class TestTextEdgeCases(UnitTestCase):
	"""Edge case tests for text condition evaluation."""

	def test_case_insensitive_contains(self):
		self.assertTrue(_eval_text("contains", "Hello WORLD", "hello"))
		self.assertTrue(_eval_text("contains", "Hello WORLD", "WORLD"))

	def test_case_insensitive_starts_with(self):
		self.assertTrue(_eval_text("starts with", "Hello", "HELLO"))

	def test_case_insensitive_ends_with(self):
		self.assertTrue(_eval_text("ends with", "Hello", "ELLO"))

	def test_none_doc_value_treated_as_empty(self):
		self.assertTrue(_eval_text("is", None, ""))
		self.assertFalse(_eval_text("contains", None, "something"))

	def test_unknown_operator_returns_false(self):
		self.assertFalse(_eval_text("unknown_op", "hello", "hello"))


class TestChangeEdgeCases(UnitTestCase):
	"""Edge case tests for change detection."""

	def test_has_changed_from_new_doc(self):
		"""'has changed from' on a new doc (no before_save) should return False."""
		doc = frappe._dict({"status": "Open"})
		self.assertFalse(_eval_change("has changed from", "status", "Draft", doc))

	def test_has_changed_with_none_values(self):
		"""Change detection should handle None values gracefully."""
		doc = frappe._dict({"status": None})
		doc._doc_before_save = frappe._dict({"status": "Open"})
		self.assertTrue(_eval_change("has changed", "status", None, doc))

	def test_has_changed_to_with_none_to_value(self):
		"""'has changed to' with None new value should work."""
		doc = frappe._dict({"status": None})
		doc._doc_before_save = frappe._dict({"status": "Open"})
		self.assertTrue(_eval_change("has changed to", "status", "", doc))

	def test_no_change_same_values(self):
		"""Same values should not count as changed."""
		doc = frappe._dict({"amount": 100})
		doc._doc_before_save = frappe._dict({"amount": 100})
		self.assertFalse(_eval_change("has changed", "amount", None, doc))
