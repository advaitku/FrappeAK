"""Tests for api/automation.py — whitelisted automation API endpoints."""

from unittest.mock import patch, MagicMock

import frappe
from frappe.tests import UnitTestCase

from frappe_ak.api.automation import (
	get_doctype_fields,
	get_field_options,
	get_operators_for_field,
	run_button_automation,
	test_automation,
	get_button_automations,
	test_whatsapp_connection,
	_text_operators,
	_numeric_operators,
	_date_operators,
	_select_operators,
	_link_operators,
	_check_operators,
)


class TestOperatorLists(UnitTestCase):
	"""Tests for operator list helper functions."""

	def test_text_operators_include_change_operators(self):
		ops = _text_operators()
		self.assertIn("is", ops)
		self.assertIn("is not", ops)
		self.assertIn("contains", ops)
		self.assertIn("has changed", ops)
		self.assertIn("has changed to", ops)
		self.assertIn("has changed from", ops)

	def test_numeric_operators(self):
		ops = _numeric_operators()
		self.assertIn("=", ops)
		self.assertIn("!=", ops)
		self.assertIn(">", ops)
		self.assertIn("<", ops)
		self.assertIn("between", ops)

	def test_date_operators_include_relative_dates(self):
		ops = _date_operators()
		self.assertIn("is today", ops)
		self.assertIn("is tomorrow", ops)
		self.assertIn("is yesterday", ops)
		self.assertIn("before", ops)
		self.assertIn("after", ops)
		self.assertIn("between", ops)

	def test_select_operators(self):
		ops = _select_operators()
		self.assertIn("is", ops)
		self.assertIn("is not", ops)
		self.assertIn("has changed to", ops)

	def test_link_operators(self):
		ops = _link_operators()
		self.assertIn("is", ops)
		self.assertIn("is empty", ops)

	def test_check_operators_only_two(self):
		ops = _check_operators()
		self.assertEqual(len(ops), 2)
		self.assertIn("is", ops)
		self.assertIn("is not", ops)


class TestGetDoctypeFields(UnitTestCase):
	"""Tests for get_doctype_fields API."""

	def test_returns_fields_for_known_doctype(self):
		"""ToDo is a core DocType, always available."""
		fields = get_doctype_fields("ToDo")
		self.assertIsInstance(fields, list)
		self.assertTrue(len(fields) > 0)

		fieldnames = [f["fieldname"] for f in fields]
		self.assertIn("status", fieldnames)

	def test_excludes_layout_fields(self):
		fields = get_doctype_fields("ToDo")
		fieldtypes = [f["fieldtype"] for f in fields]
		for excluded in ("Section Break", "Column Break", "Tab Break", "HTML", "Table", "Table MultiSelect", "Fold"):
			self.assertNotIn(excluded, fieldtypes)

	def test_field_dict_has_required_keys(self):
		fields = get_doctype_fields("ToDo")
		for f in fields:
			self.assertIn("fieldname", f)
			self.assertIn("label", f)
			self.assertIn("fieldtype", f)


class TestGetFieldOptions(UnitTestCase):
	"""Tests for get_field_options API."""

	def test_returns_options_for_select_field(self):
		"""ToDo.status is a Select field."""
		options = get_field_options("ToDo", "status")
		self.assertIsInstance(options, list)
		self.assertIn("Open", options)

	def test_returns_empty_for_non_select_field(self):
		"""ToDo.description is a Text Editor, not Select."""
		options = get_field_options("ToDo", "description")
		self.assertEqual(options, [])

	def test_returns_empty_for_nonexistent_field(self):
		options = get_field_options("ToDo", "nonexistent_field_xyz")
		self.assertEqual(options, [])


class TestGetOperatorsForField(UnitTestCase):
	"""Tests for get_operators_for_field API."""

	def test_select_field_returns_select_operators(self):
		ops = get_operators_for_field("ToDo", "status")
		self.assertIn("is", ops)
		self.assertIn("has changed to", ops)
		# Should not include numeric operators
		self.assertNotIn(">", ops)

	def test_check_field_returns_check_operators(self):
		"""Check fields should only get is/is not."""
		# Find a Check field on any standard DocType
		meta = frappe.get_meta("ToDo")
		check_fields = [f for f in meta.fields if f.fieldtype == "Check"]
		if check_fields:
			ops = get_operators_for_field("ToDo", check_fields[0].fieldname)
			self.assertEqual(len(ops), 2)

	def test_nonexistent_field_returns_text_operators(self):
		"""Unknown fields should fall back to text operators."""
		ops = get_operators_for_field("ToDo", "nonexistent_field_xyz")
		self.assertEqual(ops, _text_operators())


class TestGetButtonAutomations(UnitTestCase):
	"""Tests for get_button_automations API."""

	@patch("frappe_ak.api.automation.frappe.get_list")
	def test_queries_with_correct_filters(self, mock_get_list):
		mock_get_list.return_value = []

		get_button_automations("Sales Order")

		mock_get_list.assert_called_once()
		call_kwargs = mock_get_list.call_args
		filters = call_kwargs.kwargs.get("filters") or call_kwargs[1].get("filters")
		self.assertEqual(filters["reference_doctype"], "Sales Order")
		self.assertEqual(filters["trigger_type"], "Macro (Button)")
		self.assertEqual(filters["enabled"], 1)


class TestRunButtonAutomation(UnitTestCase):
	"""Tests for run_button_automation API."""

	@patch("frappe_ak.dispatcher.actions.execute_action")
	@patch("frappe_ak.dispatcher.conditions.evaluate_conditions", return_value=True)
	@patch("frappe_ak.api.automation.frappe.get_doc")
	def test_executes_enabled_actions(self, mock_get_doc, mock_conditions, mock_execute):
		action1 = frappe._dict({"enabled": 1, "action_type": "Update Fields"})
		action2 = frappe._dict({"enabled": 0, "action_type": "Send Email"})
		automation = frappe._dict({
			"name": "AUTO-001",
			"title": "Test Auto",
			"enabled": 1,
			"trigger_type": "Macro (Button)",
			"actions": [action1, action2],
		})
		doc = MagicMock()
		doc.check_permission = MagicMock()

		mock_get_doc.side_effect = lambda *args: {
			("AK Automation", "AUTO-001"): automation,
			("ToDo", "TODO-001"): doc,
		}.get(args, MagicMock())

		result = run_button_automation("AUTO-001", "ToDo", "TODO-001")

		self.assertEqual(result["status"], "ok")
		# Only enabled action should be executed
		mock_execute.assert_called_once_with(action1, doc, automation)

	@patch("frappe_ak.api.automation.frappe.get_doc")
	def test_throws_if_automation_disabled(self, mock_get_doc):
		automation = frappe._dict({
			"enabled": 0,
			"trigger_type": "Macro (Button)",
		})
		mock_get_doc.return_value = automation

		with self.assertRaises(Exception):
			run_button_automation("AUTO-001", "ToDo", "TODO-001")

	@patch("frappe_ak.api.automation.frappe.get_doc")
	def test_throws_if_wrong_trigger_type(self, mock_get_doc):
		automation = frappe._dict({
			"enabled": 1,
			"trigger_type": "On Create",
		})
		mock_get_doc.return_value = automation

		with self.assertRaises(Exception):
			run_button_automation("AUTO-001", "ToDo", "TODO-001")

	@patch("frappe_ak.dispatcher.conditions.evaluate_conditions", return_value=False)
	@patch("frappe_ak.api.automation.frappe.get_doc")
	def test_skips_when_conditions_not_met(self, mock_get_doc, mock_conditions):
		automation = frappe._dict({
			"enabled": 1,
			"trigger_type": "Macro (Button)",
			"actions": [],
		})
		doc = MagicMock()
		doc.check_permission = MagicMock()

		mock_get_doc.side_effect = lambda *args: {
			("AK Automation", "AUTO-001"): automation,
			("ToDo", "TODO-001"): doc,
		}.get(args, MagicMock())

		result = run_button_automation("AUTO-001", "ToDo", "TODO-001")
		self.assertEqual(result["status"], "skipped")


class TestTestAutomation(UnitTestCase):
	"""Tests for test_automation (dry-run) API."""

	@patch("frappe_ak.dispatcher.conditions.evaluate_conditions", return_value=True)
	@patch("frappe_ak.api.automation.frappe.get_doc")
	def test_with_specific_document(self, mock_get_doc, mock_conditions):
		automation = frappe._dict({
			"name": "AUTO-001",
			"reference_doctype": "ToDo",
			"actions": [
				frappe._dict({"enabled": 1}),
				frappe._dict({"enabled": 0}),
			],
		})
		doc = frappe._dict({"name": "TODO-001"})

		mock_get_doc.side_effect = lambda *args: {
			("AK Automation", "AUTO-001"): automation,
			("ToDo", "TODO-001"): doc,
		}.get(args, MagicMock())

		result = test_automation("AUTO-001", docname="TODO-001")

		self.assertEqual(result["document"], "TODO-001")
		self.assertTrue(result["conditions_met"])
		self.assertEqual(result["actions_count"], 1)

	@patch("frappe_ak.dispatcher.conditions.evaluate_conditions", return_value=False)
	@patch("frappe_ak.api.automation.frappe.get_list", return_value=["TODO-LATEST"])
	@patch("frappe_ak.api.automation.frappe.get_doc")
	def test_uses_latest_document_when_no_docname(self, mock_get_doc, mock_get_list, mock_conditions):
		automation = frappe._dict({
			"name": "AUTO-001",
			"reference_doctype": "ToDo",
			"actions": [],
		})
		doc = frappe._dict({"name": "TODO-LATEST"})

		mock_get_doc.side_effect = lambda *args: {
			("AK Automation", "AUTO-001"): automation,
			("ToDo", "TODO-LATEST"): doc,
		}.get(args, MagicMock())

		result = test_automation("AUTO-001")

		self.assertFalse(result["conditions_met"])
		self.assertIn("skipped", result["message"].lower())

	@patch("frappe_ak.api.automation.frappe.get_list", return_value=[])
	@patch("frappe_ak.api.automation.frappe.get_doc")
	def test_throws_when_no_documents_exist(self, mock_get_doc, mock_get_list):
		automation = frappe._dict({
			"name": "AUTO-001",
			"reference_doctype": "Nonexistent DocType",
			"actions": [],
		})
		mock_get_doc.return_value = automation

		with self.assertRaises(Exception):
			test_automation("AUTO-001")


class TestWhatsAppConnection(UnitTestCase):
	"""Tests for test_whatsapp_connection API."""

	@patch("frappe_ak.api.automation.frappe.db.exists", return_value=False)
	def test_returns_failure_when_app_not_installed(self, mock_exists):
		result = test_whatsapp_connection()
		self.assertFalse(result["success"])
		self.assertIn("not installed", result["error"])

	@patch("frappe_ak.api.automation.frappe.get_doc")
	@patch("frappe_ak.api.automation.frappe.get_single")
	@patch("frappe_ak.api.automation.frappe.db.exists", return_value=True)
	def test_returns_failure_when_no_default_account(self, mock_exists, mock_single, mock_get_doc):
		mock_single.return_value = frappe._dict({"default_outgoing_account": ""})

		result = test_whatsapp_connection()
		self.assertFalse(result["success"])
		self.assertIn("No default", result["error"])

	@patch("frappe_ak.api.automation.frappe.get_doc")
	@patch("frappe_ak.api.automation.frappe.get_single")
	@patch("frappe_ak.api.automation.frappe.db.exists", return_value=True)
	def test_returns_success_with_active_account(self, mock_exists, mock_single, mock_get_doc):
		mock_single.return_value = frappe._dict({"default_outgoing_account": "WA-001"})
		mock_get_doc.return_value = frappe._dict({"status": "Active"})

		result = test_whatsapp_connection()
		self.assertTrue(result["success"])
		self.assertEqual(result["account"], "WA-001")

	@patch("frappe_ak.api.automation.frappe.get_doc")
	@patch("frappe_ak.api.automation.frappe.get_single")
	@patch("frappe_ak.api.automation.frappe.db.exists", return_value=True)
	def test_returns_failure_for_inactive_account(self, mock_exists, mock_single, mock_get_doc):
		mock_single.return_value = frappe._dict({"default_outgoing_account": "WA-001"})
		mock_get_doc.return_value = frappe._dict({"status": "Disconnected"})

		result = test_whatsapp_connection()
		self.assertFalse(result["success"])
		self.assertIn("not active", result["error"])
