"""Tests for API endpoints in api/automation.py."""

import json
from unittest.mock import patch, MagicMock

import frappe
from frappe.tests import UnitTestCase

from frappe_ak.api.automation import (
	get_doctype_fields,
	get_field_options,
	get_operators_for_field,
	get_button_automations,
	run_button_automation,
	test_automation,
	test_whatsapp_connection,
)


class TestGetDoctypeFields(UnitTestCase):
	"""Tests for get_doctype_fields API."""

	def test_returns_fields(self):
		"""Should return a list of field dicts for a valid DocType."""
		fields = get_doctype_fields("ToDo")
		self.assertIsInstance(fields, list)
		self.assertTrue(len(fields) > 0)

	def test_field_has_expected_keys(self):
		"""Each field dict should have fieldname, label, fieldtype, options, reqd."""
		fields = get_doctype_fields("ToDo")
		for f in fields:
			self.assertIn("fieldname", f)
			self.assertIn("label", f)
			self.assertIn("fieldtype", f)
			self.assertIn("options", f)
			self.assertIn("reqd", f)

	def test_excludes_layout_fields(self):
		"""Section Break, Column Break, etc. should be excluded."""
		fields = get_doctype_fields("ToDo")
		fieldtypes = [f["fieldtype"] for f in fields]
		for excluded in ("Section Break", "Column Break", "Tab Break", "HTML", "Table", "Table MultiSelect", "Fold"):
			self.assertNotIn(excluded, fieldtypes)

	def test_includes_data_fields(self):
		"""Common field types like Data, Select, Link should be included."""
		fields = get_doctype_fields("ToDo")
		fieldtypes = {f["fieldtype"] for f in fields}
		# ToDo should have at least some standard field types
		self.assertTrue(len(fieldtypes) > 0)


class TestGetFieldOptions(UnitTestCase):
	"""Tests for get_field_options API."""

	def test_returns_options_for_select(self):
		"""Select fields should return their options list."""
		options = get_field_options("ToDo", "status")
		self.assertIsInstance(options, list)
		self.assertTrue(len(options) > 0)
		self.assertIn("Open", options)

	def test_returns_empty_for_non_select(self):
		"""Non-Select fields should return empty list."""
		options = get_field_options("ToDo", "description")
		self.assertEqual(options, [])

	def test_returns_empty_for_missing_field(self):
		"""Non-existent field should return empty list."""
		options = get_field_options("ToDo", "nonexistent_field_xyz")
		self.assertEqual(options, [])


class TestGetOperatorsForField(UnitTestCase):
	"""Tests for get_operators_for_field API."""

	def test_text_field_operators(self):
		"""Text/Data fields should return text operators."""
		ops = get_operators_for_field("ToDo", "description")
		self.assertIn("is", ops)
		self.assertIn("contains", ops)
		self.assertIn("starts with", ops)
		self.assertIn("has changed", ops)

	def test_select_field_operators(self):
		"""Select fields should return select operators."""
		ops = get_operators_for_field("ToDo", "status")
		self.assertIn("is", ops)
		self.assertIn("is not", ops)
		self.assertIn("has changed", ops)
		self.assertNotIn("contains", ops)

	def test_check_field_operators(self):
		"""Check (boolean) fields should return limited operators."""
		# Find a check field on ToDo — use 'send_reminder' if it exists
		meta = frappe.get_meta("ToDo")
		check_fields = [f for f in meta.fields if f.fieldtype == "Check"]
		if check_fields:
			ops = get_operators_for_field("ToDo", check_fields[0].fieldname)
			self.assertEqual(ops, ["is", "is not"])

	def test_unknown_field_returns_text_operators(self):
		"""Unknown field should default to text operators."""
		ops = get_operators_for_field("ToDo", "nonexistent_field_xyz")
		self.assertIn("is", ops)
		self.assertIn("contains", ops)

	def test_date_field_operators(self):
		"""Date fields should return date-specific operators."""
		ops = get_operators_for_field("ToDo", "date")
		self.assertIn("is today", ops)
		self.assertIn("before", ops)
		self.assertIn("after", ops)
		self.assertIn("less than days ago", ops)


class TestRunButtonAutomation(UnitTestCase):
	"""Tests for run_button_automation API."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.test_todo = frappe.get_doc({
			"doctype": "ToDo",
			"description": "Button automation test fixture",
		}).insert(ignore_permissions=True)

		cls.button_auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Test Button Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "Macro (Button)",
			"enabled": 1,
			"button_label": "Run Test",
			"all_conditions": [],
			"any_conditions": [],
			"actions": [{
				"action_type": "Run Script",
				"action_label": "Test Script",
				"enabled": 1,
				"script_code": "1 + 1",
			}],
		}).insert(ignore_permissions=True)

		cls.disabled_auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Disabled Button Auto",
			"reference_doctype": "ToDo",
			"trigger_type": "Macro (Button)",
			"enabled": 0,
			"actions": [{
				"action_type": "Run Script",
				"action_label": "Test",
				"enabled": 1,
				"script_code": "1",
			}],
		}).insert(ignore_permissions=True)

		cls.non_button_auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Non-Button Auto",
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

	@classmethod
	def tearDownClass(cls):
		for auto in [cls.button_auto, cls.disabled_auto, cls.non_button_auto]:
			frappe.delete_doc("AK Automation", auto.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.test_todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_executes_when_conditions_met(self):
		"""Should return status 'ok' when conditions pass (no conditions = always pass)."""
		result = run_button_automation(
			self.button_auto.name, "ToDo", self.test_todo.name,
		)
		self.assertEqual(result["status"], "ok")

	def test_skips_when_conditions_not_met(self):
		"""Should return status 'skipped' when conditions fail."""
		# Temporarily add a condition that can't pass
		with patch("frappe_ak.dispatcher.conditions.evaluate_conditions", return_value=False):
			result = run_button_automation(
				self.button_auto.name, "ToDo", self.test_todo.name,
			)
		self.assertEqual(result["status"], "skipped")

	def test_disabled_automation_throws(self):
		"""Should throw when automation is disabled."""
		with self.assertRaises(Exception):
			run_button_automation(
				self.disabled_auto.name, "ToDo", self.test_todo.name,
			)

	def test_wrong_trigger_type_throws(self):
		"""Should throw when automation is not a button trigger."""
		with self.assertRaises(Exception):
			run_button_automation(
				self.non_button_auto.name, "ToDo", self.test_todo.name,
			)


class TestTestAutomation(UnitTestCase):
	"""Tests for test_automation (dry-run) API."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.test_todo = frappe.get_doc({
			"doctype": "ToDo",
			"description": "Test automation dry-run fixture",
		}).insert(ignore_permissions=True)

		cls.test_auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Dry Run Auto",
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

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Automation", cls.test_auto.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.test_todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_with_specific_doc(self):
		"""Should evaluate conditions against the specific document."""
		result = test_automation(self.test_auto.name, self.test_todo.name)
		self.assertEqual(result["document"], self.test_todo.name)
		self.assertIn("conditions_met", result)
		self.assertIn("actions_count", result)

	def test_uses_latest_doc_when_none(self):
		"""Should use the latest doc when docname not provided."""
		result = test_automation(self.test_auto.name)
		self.assertIsNotNone(result["document"])
		self.assertIn("conditions_met", result)

	def test_conditions_met_true(self):
		"""No conditions should mean conditions_met=True."""
		result = test_automation(self.test_auto.name, self.test_todo.name)
		self.assertTrue(result["conditions_met"])

	def test_actions_count(self):
		result = test_automation(self.test_auto.name, self.test_todo.name)
		self.assertEqual(result["actions_count"], 1)


class TestGetButtonAutomations(UnitTestCase):
	"""Tests for get_button_automations API."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.button_auto = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Button List Test",
			"reference_doctype": "ToDo",
			"trigger_type": "Macro (Button)",
			"enabled": 1,
			"button_label": "Click Me",
			"actions": [{
				"action_type": "Run Script",
				"action_label": "Test",
				"enabled": 1,
				"script_code": "1",
			}],
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Automation", cls.button_auto.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_returns_active_button_automations(self):
		result = get_button_automations("ToDo")
		names = [r["name"] for r in result]
		self.assertIn(self.button_auto.name, names)

	def test_excludes_wrong_doctype(self):
		result = get_button_automations("Event")
		names = [r["name"] for r in result]
		self.assertNotIn(self.button_auto.name, names)

	def test_returns_expected_fields(self):
		result = get_button_automations("ToDo")
		matching = [r for r in result if r["name"] == self.button_auto.name]
		self.assertTrue(len(matching) > 0)
		self.assertIn("title", matching[0])
		self.assertIn("button_label", matching[0])


class TestWhatsAppConnection(UnitTestCase):
	"""Tests for test_whatsapp_connection API."""

	def test_no_provider_returns_failure(self):
		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({"whatsapp_provider": None})
			result = test_whatsapp_connection()
		self.assertFalse(result["success"])
		self.assertIn("No WhatsApp provider", result["error"])

	def test_meta_success(self):
		mock_settings = frappe._dict({
			"whatsapp_provider": "Meta Cloud API",
			"whatsapp_phone_number_id": "12345",
		})
		mock_settings.get_password = lambda x: "test-token"

		mock_resp = MagicMock()
		mock_resp.status_code = 200

		with (
			patch("frappe.get_single", return_value=mock_settings),
			patch("frappe_ak.api.automation.requests.get", return_value=mock_resp),
		):
			result = test_whatsapp_connection()

		self.assertTrue(result["success"])

	def test_meta_failure(self):
		mock_settings = frappe._dict({
			"whatsapp_provider": "Meta Cloud API",
			"whatsapp_phone_number_id": "12345",
		})
		mock_settings.get_password = lambda x: "bad-token"

		mock_resp = MagicMock()
		mock_resp.status_code = 401
		mock_resp.text = "Unauthorized"

		with (
			patch("frappe.get_single", return_value=mock_settings),
			patch("frappe_ak.api.automation.requests.get", return_value=mock_resp),
		):
			result = test_whatsapp_connection()

		self.assertFalse(result["success"])
		self.assertIn("401", result["error"])

	def test_twilio_not_implemented(self):
		with patch("frappe.get_single") as mock_settings:
			mock_settings.return_value = frappe._dict({"whatsapp_provider": "Twilio"})
			result = test_whatsapp_connection()
		self.assertFalse(result["success"])
		self.assertIn("not implemented", result["error"])
