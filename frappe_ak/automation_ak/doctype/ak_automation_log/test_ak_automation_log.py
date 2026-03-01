import json

import frappe
from frappe.tests import UnitTestCase


class TestAKAutomationLog(UnitTestCase):
	"""Tests for the AK Automation Log DocType."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Create a real ToDo to reference in log tests
		cls.test_todo = frappe.get_doc({
			"doctype": "ToDo",
			"description": "AK Automation Log test fixture",
		}).insert(ignore_permissions=True)

		# Create a real AK Automation to reference
		cls.test_automation = frappe.get_doc({
			"doctype": "AK Automation",
			"title": "Test Automation for Log",
			"reference_doctype": "ToDo",
			"trigger_type": "On Create",
			"enabled": 0,
			"actions": [{
				"action_type": "Update Fields",
				"action_label": "Test Action",
				"enabled": 1,
			}],
		}).insert(ignore_permissions=True)

		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		# Clean up test fixtures
		frappe.delete_doc("AK Automation", cls.test_automation.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.test_todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_log_creation(self):
		"""AK Automation Log can be created with required fields."""
		log = frappe.get_doc({
			"doctype": "AK Automation Log",
			"automation": self.test_automation.name,
			"reference_doctype": "ToDo",
			"reference_name": self.test_todo.name,
			"trigger_type": "On Create",
			"status": "Success",
			"execution_time_ms": 42.5,
		})
		log.insert(ignore_permissions=True)

		self.assertTrue(log.name)
		self.assertEqual(log.status, "Success")
		self.assertEqual(log.trigger_type, "On Create")
		self.assertEqual(log.reference_doctype, "ToDo")

		frappe.delete_doc("AK Automation Log", log.name, ignore_permissions=True)

	def test_log_failed_status(self):
		"""AK Automation Log can store error tracebacks."""
		log = frappe.get_doc({
			"doctype": "AK Automation Log",
			"automation": self.test_automation.name,
			"reference_doctype": "ToDo",
			"reference_name": self.test_todo.name,
			"trigger_type": "On Update (includes Create)",
			"status": "Failed",
			"error_traceback": "Traceback (most recent call last):\n  File ...\nValueError: test",
			"execution_time_ms": 10.0,
		})
		log.insert(ignore_permissions=True)

		self.assertEqual(log.status, "Failed")
		self.assertIn("ValueError", log.error_traceback)

		frappe.delete_doc("AK Automation Log", log.name, ignore_permissions=True)

	def test_log_actions_json(self):
		"""AK Automation Log can store actions_executed as JSON."""
		actions = [
			{"action_type": "Update Fields", "status": "Success"},
			{"action_type": "Send Email", "status": "Success"},
		]
		log = frappe.get_doc({
			"doctype": "AK Automation Log",
			"automation": self.test_automation.name,
			"reference_doctype": "ToDo",
			"reference_name": self.test_todo.name,
			"trigger_type": "On Create",
			"status": "Success",
			"actions_executed": json.dumps(actions),
			"execution_time_ms": 55.0,
		})
		log.insert(ignore_permissions=True)

		parsed = json.loads(log.actions_executed)
		self.assertEqual(len(parsed), 2)
		self.assertEqual(parsed[0]["action_type"], "Update Fields")

		frappe.delete_doc("AK Automation Log", log.name, ignore_permissions=True)

	def test_log_skipped_status(self):
		"""AK Automation Log can record skipped automations."""
		log = frappe.get_doc({
			"doctype": "AK Automation Log",
			"automation": self.test_automation.name,
			"reference_doctype": "ToDo",
			"reference_name": self.test_todo.name,
			"trigger_type": "Macro (Button)",
			"status": "Skipped",
			"execution_time_ms": 1.0,
		})
		log.insert(ignore_permissions=True)

		self.assertEqual(log.status, "Skipped")

		frappe.delete_doc("AK Automation Log", log.name, ignore_permissions=True)
