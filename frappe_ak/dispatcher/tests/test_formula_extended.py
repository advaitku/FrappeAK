"""Extended formula tests — covers evaluate_expression, _eval_conditional, evaluate_function, _build_context."""

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import today, add_days

from frappe_ak.dispatcher.formula import (
	evaluate_expression,
	evaluate_function,
	resolve_value,
	_eval_conditional,
	_eval_with_functions,
	_build_context,
	_fn_length,
)


def _mock_doc(fields):
	"""Create a mock doc object that supports as_dict() and set()."""
	doc = frappe._dict(fields)
	doc.as_dict = lambda: dict(fields)
	doc.set = lambda k, v: doc.__setitem__(k, v)
	return doc


class TestEvaluateExpression(UnitTestCase):
	"""Tests for the top-level evaluate_expression function."""

	def test_empty_expression_returns_none(self):
		doc = _mock_doc({"name": "T-1"})
		self.assertIsNone(evaluate_expression("", doc))
		self.assertIsNone(evaluate_expression(None, doc))

	def test_whitespace_only_returns_none(self):
		doc = _mock_doc({"name": "T-1"})
		self.assertIsNone(evaluate_expression("   ", doc))

	def test_simple_math(self):
		doc = _mock_doc({"amount": 100})
		result = evaluate_expression("amount * 1.1", doc)
		self.assertAlmostEqual(result, 110.0)

	def test_field_reference_division(self):
		doc = _mock_doc({"annual_revenue": 120000})
		result = evaluate_expression("annual_revenue / 12", doc)
		self.assertAlmostEqual(result, 10000.0)

	def test_if_then_else_string(self):
		doc = _mock_doc({"status": "Open"})
		result = evaluate_expression("if status == 'Open' then 'Active' else 'Inactive' end", doc)
		self.assertEqual(result, "Active")

	def test_if_then_else_false_branch(self):
		doc = _mock_doc({"status": "Closed"})
		result = evaluate_expression("if status == 'Open' then 'Active' else 'Inactive' end", doc)
		self.assertEqual(result, "Inactive")

	def test_if_then_no_else_returns_none(self):
		doc = _mock_doc({"status": "Closed"})
		result = evaluate_expression("if status == 'Open' then 'Active' end", doc)
		self.assertIsNone(result)

	def test_if_then_no_else_true(self):
		doc = _mock_doc({"status": "Open"})
		result = evaluate_expression("if status == 'Open' then 'Active' end", doc)
		self.assertEqual(result, "Active")

	def test_function_call_concat(self):
		doc = _mock_doc({"first_name": "Alice", "last_name": "Smith"})
		result = evaluate_expression("concat(first_name, ' ', last_name)", doc)
		self.assertEqual(result, "Alice Smith")

	def test_function_call_uppercase(self):
		doc = _mock_doc({"name": "hello"})
		result = evaluate_expression("uppercase(name)", doc)
		self.assertEqual(result, "HELLO")

	def test_invalid_expression_returns_string(self):
		"""Invalid expressions should return the expression as a string (fallback)."""
		doc = _mock_doc({"name": "T-1"})
		result = evaluate_expression("this is not valid python", doc)
		self.assertEqual(result, "this is not valid python")

	def test_doc_object_available(self):
		"""doc.fieldname syntax should work."""
		doc = _mock_doc({"amount": 50})
		result = evaluate_expression("doc.amount * 2", doc)
		self.assertEqual(result, 100)


class TestEvalConditional(UnitTestCase):
	"""Tests for _eval_conditional parsing."""

	def test_missing_then_throws(self):
		doc = _mock_doc({"status": "Open"})
		with self.assertRaises(Exception):
			_eval_conditional("if status == 'Open'", doc)

	def test_with_else_and_end(self):
		doc = _mock_doc({"x": 10})
		result = _eval_conditional("if x > 5 then 'big' else 'small' end", doc)
		self.assertEqual(result, "big")

	def test_without_else_with_end(self):
		doc = _mock_doc({"x": 3})
		result = _eval_conditional("if x > 5 then 'big' end", doc)
		self.assertIsNone(result)

	def test_without_end(self):
		"""Without 'end', everything after 'then' should be the then_value."""
		doc = _mock_doc({"x": 10})
		result = _eval_conditional("if x > 5 then 'big'", doc)
		self.assertEqual(result, "big")

	def test_function_in_then_clause(self):
		doc = _mock_doc({"first": "Alice", "last": "Smith"})
		result = _eval_conditional(
			"if first == 'Alice' then concat(first, ' ', last) else first end",
			doc,
		)
		self.assertEqual(result, "Alice Smith")

	def test_case_insensitive_keywords(self):
		"""if/then/else/end should be case-insensitive."""
		doc = _mock_doc({"x": 10})
		result = _eval_conditional("IF x > 5 THEN 'big' ELSE 'small' END", doc)
		self.assertEqual(result, "big")


class TestEvaluateFunction(UnitTestCase):
	"""Tests for evaluate_function (Use Function value type)."""

	def test_uppercase(self):
		update = {"function_name": "uppercase", "source_field": "name", "value": ""}
		doc = frappe._dict({"name": "hello"})
		self.assertEqual(evaluate_function(update, doc), "HELLO")

	def test_lowercase(self):
		update = {"function_name": "lowercase", "source_field": "name", "value": ""}
		doc = frappe._dict({"name": "HELLO"})
		self.assertEqual(evaluate_function(update, doc), "hello")

	def test_trim(self):
		update = {"function_name": "trim", "source_field": "name", "value": ""}
		doc = frappe._dict({"name": "  hello  "})
		self.assertEqual(evaluate_function(update, doc), "hello")

	def test_length(self):
		update = {"function_name": "length", "source_field": "name", "value": ""}
		doc = frappe._dict({"name": "hello"})
		self.assertEqual(evaluate_function(update, doc), 5)

	def test_round(self):
		update = {"function_name": "round", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": 3.7})
		self.assertEqual(evaluate_function(update, doc), 4)

	def test_abs(self):
		update = {"function_name": "abs", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": -42})
		self.assertEqual(evaluate_function(update, doc), 42)

	def test_ceil(self):
		update = {"function_name": "ceil", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": 3.2})
		self.assertEqual(evaluate_function(update, doc), 4)

	def test_floor(self):
		update = {"function_name": "floor", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": 3.8})
		self.assertEqual(evaluate_function(update, doc), 3)

	def test_unknown_function_returns_source(self):
		update = {"function_name": "nonexistent", "source_field": "name", "value": ""}
		doc = frappe._dict({"name": "hello"})
		self.assertEqual(evaluate_function(update, doc), "hello")

	def test_source_field_priority_over_value(self):
		"""source_field should take priority over value."""
		update = {"function_name": "uppercase", "source_field": "name", "value": "fallback"}
		doc = frappe._dict({"name": "from_field"})
		self.assertEqual(evaluate_function(update, doc), "FROM_FIELD")

	def test_falls_back_to_value_when_no_source(self):
		"""When source_field is empty, should use value."""
		update = {"function_name": "uppercase", "source_field": "", "value": "fallback"}
		doc = frappe._dict({})
		self.assertEqual(evaluate_function(update, doc), "FALLBACK")

	def test_concat_via_function(self):
		"""concat function should join source value as string."""
		update = {"function_name": "concat", "source_field": "name", "value": ""}
		doc = frappe._dict({"name": "hello"})
		result = evaluate_function(update, doc)
		self.assertEqual(result, "hello")


class TestBuildContext(UnitTestCase):
	"""Tests for _build_context."""

	def test_doc_fields_as_top_level(self):
		doc = _mock_doc({"status": "Open", "priority": "High"})
		ctx = _build_context(doc)
		self.assertEqual(ctx["status"], "Open")
		self.assertEqual(ctx["priority"], "High")

	def test_doc_object_available(self):
		doc = _mock_doc({"name": "T-1"})
		ctx = _build_context(doc)
		self.assertIs(ctx["doc"], doc)

	def test_frappe_available(self):
		doc = _mock_doc({})
		ctx = _build_context(doc)
		self.assertIs(ctx["frappe"], frappe)

	def test_helper_functions_available(self):
		doc = _mock_doc({})
		ctx = _build_context(doc)
		self.assertTrue(callable(ctx["today"]))
		self.assertTrue(callable(ctx["add_days"]))
		self.assertTrue(callable(ctx["getdate"]))
		self.assertTrue(callable(ctx["flt"]))
		self.assertTrue(callable(ctx["cint"]))
		self.assertTrue(callable(ctx["now"]))


class TestResolveValueExtended(UnitTestCase):
	"""Extended tests for resolve_value edge cases."""

	def test_expression_value_type(self):
		doc = _mock_doc({"amount": 100})
		result = resolve_value("Expression", {"value": "amount * 2"}, doc)
		self.assertEqual(result, 200)

	def test_use_function_value_type(self):
		doc = frappe._dict({"name": "hello"})
		result = resolve_value("Use Function", {
			"function_name": "uppercase",
			"source_field": "name",
			"value": "",
		}, doc)
		self.assertEqual(result, "HELLO")

	def test_days_key_fallback(self):
		"""Should fall back to 'days' key when 'days_offset' is missing."""
		doc = frappe._dict({})
		result = resolve_value("Today + N Days", {"days": 5}, doc)
		self.assertEqual(result, add_days(today(), 5))

	def test_unknown_value_type_returns_value(self):
		"""Unknown value types should fall through and return the value."""
		doc = frappe._dict({})
		result = resolve_value("Some Unknown Type", {"value": "fallback"}, doc)
		self.assertEqual(result, "fallback")


class TestFnLength(UnitTestCase):
	"""Tests for _fn_length."""

	def test_normal_string(self):
		self.assertEqual(_fn_length("hello"), 5)

	def test_empty_string(self):
		self.assertEqual(_fn_length(""), 0)

	def test_none(self):
		self.assertEqual(_fn_length(None), 0)

	def test_numeric_input(self):
		self.assertEqual(_fn_length(12345), 5)


class TestFormulaFunctionsExtended(UnitTestCase):
	"""Tests for ceil, floor, today(), now() functions."""

	def test_ceil_via_evaluate_function(self):
		"""ceil(3.2) should return 4."""
		update = {"function_name": "ceil", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": 3.2})
		self.assertEqual(evaluate_function(update, doc), 4)

	def test_floor_via_evaluate_function(self):
		"""floor(3.8) should return 3."""
		update = {"function_name": "floor", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": 3.8})
		self.assertEqual(evaluate_function(update, doc), 3)

	def test_ceil_with_negative(self):
		"""ceil(-3.2) should return -3."""
		update = {"function_name": "ceil", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": -3.2})
		self.assertEqual(evaluate_function(update, doc), -3)

	def test_floor_with_negative(self):
		"""floor(-3.8) should return -4."""
		update = {"function_name": "floor", "source_field": "amount", "value": ""}
		doc = frappe._dict({"amount": -3.8})
		self.assertEqual(evaluate_function(update, doc), -4)

	def test_today_function_in_expression(self):
		"""today() should return today's date in expressions."""
		doc = _mock_doc({"name": "T-1"})
		result = evaluate_expression("today()", doc)
		self.assertEqual(str(result), today())

	def test_now_function_available(self):
		"""now() should return a datetime, not None or error."""
		doc = _mock_doc({"name": "T-1"})
		result = evaluate_expression("now()", doc)
		self.assertIsNotNone(result)
