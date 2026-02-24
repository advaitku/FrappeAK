import json
from unittest.mock import MagicMock, patch, call

import frappe
from frappe.tests import UnitTestCase

from frappe_ak.dispatcher.actions import execute_action, ACTION_MODULE_MAP


def _mock_doc(fields):
	"""Create a mock doc that supports as_dict() and set() like a Document."""
	doc = frappe._dict(fields)
	doc.as_dict = lambda: dict(fields)
	doc.set = lambda k, v: doc.__setitem__(k, v)
	return doc


class TestExecuteActionDispatch(UnitTestCase):
	"""Tests for the action dispatcher routing in __init__.py."""

	def _make_action(self, action_type, **kwargs):
		d = frappe._dict({
			"action_type": action_type,
			"action_label": action_type,
			"enabled": 1,
			"idx": 1,
			"field_updates_json": None,
			"target_doctype": None,
			"record_values_json": None,
			"http_url": None,
			"http_method": "GET",
			"http_headers": None,
			"http_body": None,
			"script_code": None,
			"email_to": None,
			"email_cc": None,
			"email_bcc": None,
			"email_subject": None,
			"email_body": None,
			"email_template": None,
			"email_from": None,
			"email_reply_to": None,
			"attach_print": 0,
			"print_format": None,
			"wa_to": None,
			"wa_template_name": None,
			"wa_message_body": None,
		})
		d.update(kwargs)
		return d

	def test_all_action_types_have_modules(self):
		"""Every action type in the map should resolve to an importable module."""
		expected_types = [
			"Send Email", "Send WhatsApp", "Update Fields",
			"Create Record", "Create Todo", "Create Event",
			"HTTP Request", "Run Script",
		]
		for at in expected_types:
			self.assertIn(at, ACTION_MODULE_MAP)

	def test_unknown_action_type_throws(self):
		"""An unrecognized action type should raise an error."""
		action = self._make_action("Nonexistent Action")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-1", "trigger_type": "On Create"})

		with self.assertRaises(Exception):
			execute_action(action, doc, auto)

	def test_routes_to_correct_module(self):
		"""execute_action should call the correct module's execute function."""
		action = self._make_action("Run Script", script_code="")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-1", "trigger_type": "On Create"})

		with patch("frappe_ak.dispatcher.actions.run_script.execute", return_value="Script executed") as mock_exec:
			result = execute_action(action, doc, auto)
			mock_exec.assert_called_once_with(action, doc, auto)
			self.assertEqual(result, "Script executed")


class TestUpdateFieldsAction(UnitTestCase):
	"""Tests for update_fields.py action handler."""

	def _make_action(self, json_updates=None, **kwargs):
		d = frappe._dict({
			"action_type": "Update Fields",
			"action_label": "Update",
			"enabled": 1,
			"idx": 1,
			"field_updates_json": json.dumps(json_updates) if json_updates else None,
		})
		d.update(kwargs)
		return d

	def _make_auto(self, trigger_type="On Create", field_updates=None):
		return frappe._dict({
			"name": "AUTO-UF",
			"trigger_type": trigger_type,
			"field_updates": field_updates or [],
		})

	def test_static_value_update(self):
		"""Static value should be set on the document."""
		updates = [{"target_field": "status", "value_type": "Static Value", "value": "Closed"}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "status": "Open"})
		auto = self._make_auto()

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			result = execute(action, doc, auto)

		self.assertIn("status", result)
		self.assertEqual(doc.status, "Closed")

	def test_use_field_copies_value(self):
		"""'Use Field' should copy from another field on the doc."""
		updates = [{"target_field": "description", "value_type": "Use Field", "source_field": "status"}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "status": "Open", "description": ""})
		auto = self._make_auto()

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			result = execute(action, doc, auto)

		self.assertEqual(doc.description, "Open")

	def test_today_value(self):
		"""'Today' should set to today's date."""
		updates = [{"target_field": "date", "value_type": "Today"}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "date": None})
		auto = self._make_auto()

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			execute(action, doc, auto)

		self.assertEqual(doc.date, frappe.utils.today())

	def test_today_plus_n_days(self):
		"""'Today + N Days' should add N days."""
		updates = [{"target_field": "date", "value_type": "Today + N Days", "days_offset": 7}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "date": None})
		auto = self._make_auto()

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			execute(action, doc, auto)

		expected = frappe.utils.add_days(frappe.utils.today(), 7)
		self.assertEqual(doc.date, expected)

	def test_today_minus_n_days(self):
		"""'Today - N Days' should subtract N days."""
		updates = [{"target_field": "date", "value_type": "Today - N Days", "days_offset": 3}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "date": None})
		auto = self._make_auto()

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			execute(action, doc, auto)

		expected = frappe.utils.add_days(frappe.utils.today(), -3)
		self.assertEqual(doc.date, expected)

	def test_current_user(self):
		"""'Current User' should resolve to frappe.session.user."""
		updates = [{"target_field": "allocated_to", "value_type": "Current User"}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "allocated_to": None})
		auto = self._make_auto()

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			execute(action, doc, auto)

		self.assertEqual(doc.allocated_to, frappe.session.user)

	def test_clear_sets_none(self):
		"""'Clear' should set the field to None."""
		updates = [{"target_field": "description", "value_type": "Clear"}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "description": "old value"})
		auto = self._make_auto()

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			execute(action, doc, auto)

		self.assertIsNone(doc.description)

	def test_no_updates_returns_message(self):
		"""When no updates defined, should return info message."""
		action = self._make_action(json_updates=None)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1"})
		auto = self._make_auto(field_updates=[])

		from frappe_ak.dispatcher.actions.update_fields import execute
		result = execute(action, doc, auto)
		self.assertEqual(result, "No field updates defined")

	def test_db_set_for_on_create(self):
		"""On Create trigger should use db_set to avoid re-triggering."""
		updates = [{"target_field": "status", "value_type": "Static Value", "value": "Closed"}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "status": "Open"})
		auto = self._make_auto(trigger_type="On Create")

		with patch("frappe.db.set_value") as mock_set:
			from frappe_ak.dispatcher.actions.update_fields import execute
			execute(action, doc, auto)
			mock_set.assert_called_once()

	def test_doc_set_for_before_save(self):
		"""before_save trigger should use doc.set (no db_set)."""
		updates = [{"target_field": "status", "value_type": "Static Value", "value": "Closed"}]
		action = self._make_action(json_updates=updates)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "status": "Open"})
		auto = self._make_auto(trigger_type="before_save")

		with patch("frappe.db.set_value") as mock_set:
			from frappe_ak.dispatcher.actions.update_fields import execute
			execute(action, doc, auto)
			mock_set.assert_not_called()

		self.assertEqual(doc.status, "Closed")

	def test_child_table_fallback(self):
		"""When JSON is empty, should fall back to AK Field Update child table."""
		child = frappe._dict({
			"parent_action_idx": 1,
			"target_field": "status",
			"value_type": "Static Value",
			"value": "Closed",
		})
		child.as_dict = lambda: {
			"parent_action_idx": 1,
			"target_field": "status",
			"value_type": "Static Value",
			"value": "Closed",
		}

		action = self._make_action(json_updates=None)
		doc = _mock_doc({"doctype": "ToDo", "name": "T-1", "status": "Open"})
		auto = self._make_auto(field_updates=[child])

		with patch("frappe.db.set_value"):
			from frappe_ak.dispatcher.actions.update_fields import execute
			result = execute(action, doc, auto)

		self.assertIn("status", result)
		self.assertEqual(doc.status, "Closed")


class TestCreateRecordAction(UnitTestCase):
	"""Tests for create_record.py action handler."""

	def _make_action(self, target_doctype=None, values_json=None):
		return frappe._dict({
			"action_type": "Create Record",
			"target_doctype": target_doctype,
			"record_values_json": json.dumps(values_json) if values_json else None,
		})

	def test_creates_doc_with_dict_values(self):
		"""Should create a new doc using dict-format JSON values."""
		action = self._make_action(
			target_doctype="ToDo",
			values_json={"description": "Auto-created"},
		)
		doc = frappe._dict({"doctype": "Event", "name": "EVT-1"})
		auto = frappe._dict({"name": "AUTO-CR"})

		from frappe_ak.dispatcher.actions.create_record import execute
		result = execute(action, doc, auto)

		self.assertIn("Created ToDo", result)
		# Clean up
		todo_name = result.split(": ")[1]
		frappe.delete_doc("ToDo", todo_name, ignore_permissions=True, force=True)

	def test_creates_doc_with_list_values(self):
		"""Should create a new doc using list-format JSON values."""
		action = self._make_action(
			target_doctype="ToDo",
			values_json=[{"fieldname": "description", "value": "List format"}],
		)
		doc = frappe._dict({"doctype": "Event", "name": "EVT-1"})
		auto = frappe._dict({"name": "AUTO-CR"})

		from frappe_ak.dispatcher.actions.create_record import execute
		result = execute(action, doc, auto)

		self.assertIn("Created ToDo", result)
		todo_name = result.split(": ")[1]
		frappe.delete_doc("ToDo", todo_name, ignore_permissions=True, force=True)

	def test_jinja_template_in_values(self):
		"""Jinja templates in values should be rendered with doc context."""
		action = self._make_action(
			target_doctype="ToDo",
			values_json={"description": "Follow up on {{ doc.name }}"},
		)
		doc = frappe._dict({"doctype": "Event", "name": "EVT-999"})
		auto = frappe._dict({"name": "AUTO-CR"})

		from frappe_ak.dispatcher.actions.create_record import execute
		result = execute(action, doc, auto)

		todo_name = result.split(": ")[1]
		todo = frappe.get_doc("ToDo", todo_name)
		self.assertIn("EVT-999", todo.description)
		frappe.delete_doc("ToDo", todo_name, ignore_permissions=True, force=True)

	def test_missing_target_doctype_throws(self):
		"""Missing target_doctype should throw an error."""
		action = self._make_action(target_doctype=None)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-CR"})

		from frappe_ak.dispatcher.actions.create_record import execute
		with self.assertRaises(Exception):
			execute(action, doc, auto)

	def test_invalid_json_throws(self):
		"""Invalid JSON in record_values_json should throw."""
		action = frappe._dict({
			"action_type": "Create Record",
			"target_doctype": "ToDo",
			"record_values_json": "not valid json{{{",
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-CR"})

		from frappe_ak.dispatcher.actions.create_record import execute
		with self.assertRaises(Exception):
			execute(action, doc, auto)


class TestCreateTodoAction(UnitTestCase):
	"""Tests for create_todo.py action handler."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		# Create a real ToDo to use as the triggering document (for Dynamic Link validation)
		cls.trigger_doc = frappe.get_doc({
			"doctype": "ToDo",
			"description": "Trigger doc for create_todo tests",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("ToDo", cls.trigger_doc.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_creates_todo_with_defaults(self):
		"""Should create a ToDo with default values."""
		action = frappe._dict({
			"action_type": "Create Todo",
			"record_values_json": None,
		})
		doc = self.trigger_doc
		auto = frappe._dict({"name": "AUTO-TD"})

		from frappe_ak.dispatcher.actions.create_todo import execute
		result = execute(action, doc, auto)

		self.assertIn("Created ToDo", result)
		todo_name = result.split(": ")[1]
		todo = frappe.get_doc("ToDo", todo_name)
		self.assertIn(doc.name, todo.description)
		self.assertEqual(todo.reference_type, "ToDo")
		self.assertEqual(todo.reference_name, doc.name)
		frappe.delete_doc("ToDo", todo_name, ignore_permissions=True, force=True)

	def test_custom_config(self):
		"""Should use custom description, priority, date from config."""
		config = {
			"description": "Custom task",
			"priority": "High",
			"date": "2026-12-31",
		}
		action = frappe._dict({
			"action_type": "Create Todo",
			"record_values_json": json.dumps(config),
		})
		doc = self.trigger_doc
		auto = frappe._dict({"name": "AUTO-TD"})

		from frappe_ak.dispatcher.actions.create_todo import execute
		result = execute(action, doc, auto)

		todo_name = result.split(": ")[1]
		todo = frappe.get_doc("ToDo", todo_name)
		self.assertEqual(todo.description, "Custom task")
		self.assertEqual(todo.priority, "High")
		frappe.delete_doc("ToDo", todo_name, ignore_permissions=True, force=True)

	def test_jinja_in_description(self):
		"""Jinja templates in description should be rendered."""
		config = {"description": "Follow up: {{ doc.name }}"}
		action = frappe._dict({
			"action_type": "Create Todo",
			"record_values_json": json.dumps(config),
		})
		doc = self.trigger_doc
		auto = frappe._dict({"name": "AUTO-TD"})

		from frappe_ak.dispatcher.actions.create_todo import execute
		result = execute(action, doc, auto)

		todo_name = result.split(": ")[1]
		todo = frappe.get_doc("ToDo", todo_name)
		self.assertIn(doc.name, todo.description)
		frappe.delete_doc("ToDo", todo_name, ignore_permissions=True, force=True)


class TestCreateEventAction(UnitTestCase):
	"""Tests for create_event.py action handler."""

	def test_creates_event_with_defaults(self):
		"""Should create an Event with default values."""
		action = frappe._dict({
			"action_type": "Create Event",
			"record_values_json": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-EV", "title": "Test Auto"})

		from frappe_ak.dispatcher.actions.create_event import execute
		result = execute(action, doc, auto)

		self.assertIn("Created Event", result)
		event_name = result.split(": ")[1]
		event = frappe.get_doc("Event", event_name)
		self.assertIn("Test Auto", event.subject)
		self.assertEqual(event.event_type, "Private")
		frappe.delete_doc("Event", event_name, ignore_permissions=True, force=True)

	def test_custom_config(self):
		"""Should use custom subject, event_type from config."""
		config = {
			"subject": "Custom Event",
			"event_type": "Public",
		}
		action = frappe._dict({
			"action_type": "Create Event",
			"record_values_json": json.dumps(config),
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-2"})
		auto = frappe._dict({"name": "AUTO-EV", "title": "Test"})

		from frappe_ak.dispatcher.actions.create_event import execute
		result = execute(action, doc, auto)

		event_name = result.split(": ")[1]
		event = frappe.get_doc("Event", event_name)
		self.assertEqual(event.subject, "Custom Event")
		self.assertEqual(event.event_type, "Public")
		frappe.delete_doc("Event", event_name, ignore_permissions=True, force=True)

	def test_jinja_in_subject(self):
		"""Jinja templates in subject should be rendered."""
		config = {"subject": "Event for {{ doc.name }}"}
		action = frappe._dict({
			"action_type": "Create Event",
			"record_values_json": json.dumps(config),
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-JINJA"})
		auto = frappe._dict({"name": "AUTO-EV", "title": "Test"})

		from frappe_ak.dispatcher.actions.create_event import execute
		result = execute(action, doc, auto)

		event_name = result.split(": ")[1]
		event = frappe.get_doc("Event", event_name)
		self.assertIn("T-JINJA", event.subject)
		frappe.delete_doc("Event", event_name, ignore_permissions=True, force=True)


class TestHTTPRequestAction(UnitTestCase):
	"""Tests for http_request.py action handler."""

	def _make_action(self, url="https://example.com/api", method="GET", headers=None, body=None):
		return frappe._dict({
			"action_type": "HTTP Request",
			"http_url": url,
			"http_method": method,
			"http_headers": json.dumps(headers) if headers else None,
			"http_body": json.dumps(body) if isinstance(body, (dict, list)) else body,
		})

	def test_get_request(self):
		"""GET request should be made with correct URL."""
		action = self._make_action(url="https://example.com/test", method="GET")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 200

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp) as mock_req:
			from frappe_ak.dispatcher.actions.http_request import execute
			result = execute(action, doc, auto)

		mock_req.assert_called_once()
		call_kwargs = mock_req.call_args
		self.assertEqual(call_kwargs[1]["method"], "GET")
		self.assertEqual(call_kwargs[1]["url"], "https://example.com/test")
		self.assertIn("200", result)

	def test_post_request_with_json_body(self):
		"""POST request should send JSON body."""
		action = self._make_action(
			url="https://example.com/api",
			method="POST",
			body={"key": "value"},
		)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 201

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp) as mock_req:
			from frappe_ak.dispatcher.actions.http_request import execute
			result = execute(action, doc, auto)

		call_kwargs = mock_req.call_args[1]
		self.assertEqual(call_kwargs["method"], "POST")
		self.assertEqual(call_kwargs["json"], {"key": "value"})

	def test_jinja_in_url(self):
		"""Jinja templates in URL should be rendered."""
		action = self._make_action(url="https://example.com/{{ doc.name }}")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-123"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 200

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp) as mock_req:
			from frappe_ak.dispatcher.actions.http_request import execute
			execute(action, doc, auto)

		call_kwargs = mock_req.call_args[1]
		self.assertIn("T-123", call_kwargs["url"])

	def test_custom_headers_merged(self):
		"""Custom headers should be merged with defaults."""
		action = self._make_action(headers={"X-Custom": "value123"})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 200

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp) as mock_req:
			from frappe_ak.dispatcher.actions.http_request import execute
			execute(action, doc, auto)

		call_kwargs = mock_req.call_args[1]
		self.assertEqual(call_kwargs["headers"]["X-Custom"], "value123")
		self.assertEqual(call_kwargs["headers"]["Content-Type"], "application/json")

	def test_missing_url_throws(self):
		"""Empty URL should throw an error."""
		action = self._make_action(url="")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		from frappe_ak.dispatcher.actions.http_request import execute
		with self.assertRaises(Exception):
			execute(action, doc, auto)

	def test_timeout_set(self):
		"""Request should have a 30s timeout."""
		action = self._make_action()
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 200

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp) as mock_req:
			from frappe_ak.dispatcher.actions.http_request import execute
			execute(action, doc, auto)

		self.assertEqual(mock_req.call_args[1]["timeout"], 30)

	def test_network_timeout_raises(self):
		"""requests.Timeout should propagate (not swallowed)."""
		import requests as req_lib
		action = frappe._dict({
			"action_type": "HTTP Request",
			"http_url": "https://example.com/api",
			"http_method": "GET",
			"http_headers": None,
			"http_body": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", side_effect=req_lib.exceptions.Timeout("timed out")):
			from frappe_ak.dispatcher.actions.http_request import execute
			with self.assertRaises(req_lib.exceptions.Timeout):
				execute(action, doc, auto)

	def test_connection_error_raises(self):
		"""requests.ConnectionError should propagate."""
		import requests as req_lib
		action = frappe._dict({
			"action_type": "HTTP Request",
			"http_url": "https://example.com/api",
			"http_method": "GET",
			"http_headers": None,
			"http_body": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", side_effect=req_lib.exceptions.ConnectionError("refused")):
			from frappe_ak.dispatcher.actions.http_request import execute
			with self.assertRaises(req_lib.exceptions.ConnectionError):
				execute(action, doc, auto)

	def test_http_500_still_returns_success_message(self):
		"""HTTP 500 responses still return success message (code doesn't check status)."""
		action = frappe._dict({
			"action_type": "HTTP Request",
			"http_url": "https://example.com/api",
			"http_method": "GET",
			"http_headers": None,
			"http_body": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 500

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp):
			from frappe_ak.dispatcher.actions.http_request import execute
			result = execute(action, doc, auto)

		self.assertIn("500", result)

	def test_malformed_json_headers_ignored(self):
		"""Invalid JSON in headers should be silently ignored, keeping defaults."""
		action = frappe._dict({
			"action_type": "HTTP Request",
			"http_url": "https://example.com/api",
			"http_method": "GET",
			"http_headers": "not valid json",
			"http_body": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 200

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp) as mock_req:
			from frappe_ak.dispatcher.actions.http_request import execute
			execute(action, doc, auto)

		headers = mock_req.call_args[1]["headers"]
		self.assertEqual(headers, {"Content-Type": "application/json"})

	def test_malformed_json_body_sent_as_string(self):
		"""Non-JSON body should be sent as raw string data, not json."""
		action = frappe._dict({
			"action_type": "HTTP Request",
			"http_url": "https://example.com/api",
			"http_method": "POST",
			"http_headers": None,
			"http_body": "plain text body",
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-HTTP"})

		mock_resp = MagicMock()
		mock_resp.status_code = 200

		with patch("frappe_ak.dispatcher.actions.http_request.requests.request", return_value=mock_resp) as mock_req:
			from frappe_ak.dispatcher.actions.http_request import execute
			execute(action, doc, auto)

		call_kwargs = mock_req.call_args[1]
		self.assertEqual(call_kwargs["data"], "plain text body")
		self.assertIsNone(call_kwargs["json"])


class TestRunScriptAction(UnitTestCase):
	"""Tests for run_script.py action handler."""

	def test_empty_script_returns_message(self):
		"""Empty script should return info message, not execute."""
		action = frappe._dict({"action_type": "Run Script", "script_code": ""})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-RS"})

		from frappe_ak.dispatcher.actions.run_script import execute
		result = execute(action, doc, auto)
		self.assertEqual(result, "No script code provided")

	def test_none_script_returns_message(self):
		action = frappe._dict({"action_type": "Run Script", "script_code": None})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-RS"})

		from frappe_ak.dispatcher.actions.run_script import execute
		result = execute(action, doc, auto)
		self.assertEqual(result, "No script code provided")

	def test_simple_expression(self):
		"""Simple safe_eval expression should execute."""
		action = frappe._dict({"action_type": "Run Script", "script_code": "1 + 1"})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-RS"})

		from frappe_ak.dispatcher.actions.run_script import execute
		result = execute(action, doc, auto)
		self.assertEqual(result, "Script executed")

	def test_multiline_script(self):
		"""Multi-line scripts should fall back to exec."""
		script = "x = 1\ny = 2\nz = x + y"
		action = frappe._dict({"action_type": "Run Script", "script_code": script})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-RS"})

		from frappe_ak.dispatcher.actions.run_script import execute
		result = execute(action, doc, auto)
		self.assertEqual(result, "Script executed")

	def test_script_has_doc_context(self):
		"""Script should have access to doc object."""
		script = "doc.get('name')"
		action = frappe._dict({"action_type": "Run Script", "script_code": script})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-RS"})

		from frappe_ak.dispatcher.actions.run_script import execute
		result = execute(action, doc, auto)
		self.assertEqual(result, "Script executed")

	def test_script_context_has_automation(self):
		"""Script should have access to the automation object."""
		script = "automation.get('name')"
		action = frappe._dict({"action_type": "Run Script", "script_code": script})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-RS", "title": "My Automation"})

		from frappe_ak.dispatcher.actions.run_script import execute
		result = execute(action, doc, auto)
		self.assertEqual(result, "Script executed")


class TestSendEmailAction(UnitTestCase):
	"""Tests for send_email.py action handler."""

	def _make_action(self, **kwargs):
		d = frappe._dict({
			"action_type": "Send Email",
			"email_to": "test@example.com",
			"email_cc": None,
			"email_bcc": None,
			"email_subject": "Test Subject",
			"email_body": "Test Body",
			"email_template": None,
			"email_from": None,
			"email_reply_to": None,
			"attach_print": 0,
			"print_format": None,
		})
		d.update(kwargs)
		return d

	def test_sends_email_with_basic_fields(self):
		"""Should call frappe.sendmail with correct recipients and subject."""
		action = self._make_action()
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-EM", "title": "Test"})

		with patch("frappe.sendmail") as mock_send:
			from frappe_ak.dispatcher.actions.send_email import execute
			result = execute(action, doc, auto)

		mock_send.assert_called_once()
		call_kwargs = mock_send.call_args[1]
		self.assertEqual(call_kwargs["recipients"], ["test@example.com"])
		self.assertEqual(call_kwargs["subject"], "Test Subject")
		self.assertIn("test@example.com", result)

	def test_jinja_in_subject(self):
		"""Jinja templates in subject should be rendered."""
		action = self._make_action(email_subject="RE: {{ doc.name }}")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-999"})
		auto = frappe._dict({"name": "AUTO-EM", "title": "Test"})

		with patch("frappe.sendmail") as mock_send:
			from frappe_ak.dispatcher.actions.send_email import execute
			execute(action, doc, auto)

		call_kwargs = mock_send.call_args[1]
		self.assertIn("T-999", call_kwargs["subject"])

	def test_no_recipients_returns_none(self):
		"""No recipients should log error and return None."""
		action = self._make_action(email_to="")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-EM", "title": "Test"})

		with patch("frappe.sendmail") as mock_send, patch("frappe.log_error"):
			from frappe_ak.dispatcher.actions.send_email import execute
			result = execute(action, doc, auto)

		mock_send.assert_not_called()
		self.assertIsNone(result)

	def test_cc_bcc_split(self):
		"""CC and BCC should be split on comma."""
		action = self._make_action(
			email_cc="cc1@test.com, cc2@test.com",
			email_bcc="bcc@test.com",
		)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-EM", "title": "Test"})

		with patch("frappe.sendmail") as mock_send:
			from frappe_ak.dispatcher.actions.send_email import execute
			execute(action, doc, auto)

		call_kwargs = mock_send.call_args[1]
		self.assertEqual(call_kwargs["cc"], ["cc1@test.com", "cc2@test.com"])
		self.assertEqual(call_kwargs["bcc"], ["bcc@test.com"])

	def test_newline_separated_emails(self):
		"""Emails separated by newlines should be split correctly."""
		from frappe_ak.dispatcher.actions.send_email import _split_emails
		result = _split_emails("a@test.com\nb@test.com\nc@test.com")
		self.assertEqual(result, ["a@test.com", "b@test.com", "c@test.com"])

	def test_split_emails_empty(self):
		from frappe_ak.dispatcher.actions.send_email import _split_emails
		self.assertEqual(_split_emails(""), [])
		self.assertEqual(_split_emails(None), [])

	def test_attach_print_included(self):
		"""When attach_print=1 and print_format set, attachment should be included."""
		action = self._make_action(attach_print=1, print_format="Standard")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-EM", "title": "Test"})

		with (
			patch("frappe.sendmail") as mock_send,
			patch("frappe.attach_print", return_value={"fname": "doc.pdf"}) as mock_attach,
		):
			from frappe_ak.dispatcher.actions.send_email import execute
			execute(action, doc, auto)

		mock_attach.assert_called_once_with("ToDo", "T-1", print_format="Standard")
		call_kwargs = mock_send.call_args[1]
		self.assertEqual(call_kwargs["attachments"], [{"fname": "doc.pdf"}])

	def test_attach_print_skipped_without_format(self):
		"""When attach_print=1 but no print_format, no attachment should be added."""
		action = self._make_action(attach_print=1, print_format="")
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-EM", "title": "Test"})

		with (
			patch("frappe.sendmail") as mock_send,
			patch("frappe.attach_print") as mock_attach,
		):
			from frappe_ak.dispatcher.actions.send_email import execute
			execute(action, doc, auto)

		mock_attach.assert_not_called()
		call_kwargs = mock_send.call_args[1]
		self.assertIsNone(call_kwargs["attachments"])

	def test_email_template_used(self):
		"""When email_template is set, template subject/body should be used."""
		action = self._make_action(
			email_template="My Template",
			email_subject="",
			email_body="should not be used",
		)
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-EM", "title": "Test"})

		mock_template = frappe._dict({
			"subject": "Template Subject: {{ doc.name }}",
			"response": "Template Body: {{ doc.name }}",
		})

		with (
			patch("frappe.sendmail") as mock_send,
			patch("frappe.get_doc", return_value=mock_template),
		):
			from frappe_ak.dispatcher.actions.send_email import execute
			execute(action, doc, auto)

		call_kwargs = mock_send.call_args[1]
		self.assertIn("T-1", call_kwargs["subject"])
		self.assertIn("Template Body", call_kwargs["message"])


class TestSendWhatsAppAction(UnitTestCase):
	"""Tests for send_whatsapp.py action handler (via frappe_whatsapp)."""

	def test_not_installed_throws(self):
		"""Missing frappe_whatsapp app should throw."""
		action = frappe._dict({
			"action_type": "Send WhatsApp",
			"wa_to": "+1234567890",
			"wa_message_body": "Hello",
			"wa_template_name": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-WA"})

		with patch("frappe.db.exists", return_value=False):
			from frappe_ak.dispatcher.actions.send_whatsapp import execute
			with self.assertRaises(Exception):
				execute(action, doc, auto)

	def test_no_phone_returns_none(self):
		"""Empty phone number should log error and return None."""
		action = frappe._dict({
			"action_type": "Send WhatsApp",
			"wa_to": "",
			"wa_message_body": "Hello",
			"wa_template_name": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-WA"})

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.log_error"),
		):
			from frappe_ak.dispatcher.actions.send_whatsapp import execute
			result = execute(action, doc, auto)
			self.assertIsNone(result)

	def test_phone_normalization(self):
		"""Phone numbers should be normalized."""
		from frappe_ak.dispatcher.actions.send_whatsapp import _normalize_phone

		self.assertEqual(_normalize_phone("+1 (234) 567-890"), "+1234567890")
		self.assertEqual(_normalize_phone("1234567890"), "1234567890")
		self.assertEqual(_normalize_phone("+91-98765-43210"), "+919876543210")
		self.assertEqual(_normalize_phone("  +1234  "), "+1234")

	def test_text_message_creates_whatsapp_doc(self):
		"""Text message should create a WhatsApp Message doc with correct fields."""
		action = frappe._dict({
			"action_type": "Send WhatsApp",
			"wa_to": "+1234567890",
			"wa_message_body": "Hello World",
			"wa_template_name": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-WA"})

		mock_msg_doc = MagicMock()
		mock_msg_doc.name = "WA-MSG-001"

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.new_doc", return_value=mock_msg_doc) as mock_new_doc,
		):
			from frappe_ak.dispatcher.actions.send_whatsapp import execute
			result = execute(action, doc, auto)

		mock_new_doc.assert_called_once_with("WhatsApp Message")
		# Check first update call — common fields
		first_update = mock_msg_doc.update.call_args_list[0][0][0]
		self.assertEqual(first_update["type"], "Outgoing")
		self.assertEqual(first_update["to"], "+1234567890")
		self.assertEqual(first_update["reference_doctype"], "ToDo")
		self.assertEqual(first_update["reference_name"], "T-1")
		# Check second update call — text message fields
		second_update = mock_msg_doc.update.call_args_list[1][0][0]
		self.assertEqual(second_update["content_type"], "text")
		self.assertEqual(second_update["message"], "Hello World")
		mock_msg_doc.insert.assert_called_once_with(ignore_permissions=True)
		self.assertIn("WA-MSG-001", result)

	def test_template_message_creates_whatsapp_doc(self):
		"""Template message should create a WhatsApp Message doc with template fields."""
		action = frappe._dict({
			"action_type": "Send WhatsApp",
			"wa_to": "+1234567890",
			"wa_message_body": None,
			"wa_template_name": "hello_world",
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		auto = frappe._dict({"name": "AUTO-WA"})

		mock_msg_doc = MagicMock()
		mock_msg_doc.name = "WA-MSG-002"

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.new_doc", return_value=mock_msg_doc),
		):
			from frappe_ak.dispatcher.actions.send_whatsapp import execute
			execute(action, doc, auto)

		# Check second update call — template fields
		second_update = mock_msg_doc.update.call_args_list[1][0][0]
		self.assertEqual(second_update["message_type"], "Template")
		self.assertEqual(second_update["use_template"], 1)
		self.assertEqual(second_update["template"], "hello_world")
		mock_msg_doc.insert.assert_called_once_with(ignore_permissions=True)

	def test_jinja_rendering_in_phone(self):
		"""Phone number should support Jinja templates."""
		action = frappe._dict({
			"action_type": "Send WhatsApp",
			"wa_to": "{{ doc.phone }}",
			"wa_message_body": "Hello",
			"wa_template_name": None,
		})
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1", "phone": "+919876543210"})
		auto = frappe._dict({"name": "AUTO-WA"})

		mock_msg_doc = MagicMock()
		mock_msg_doc.name = "WA-MSG-003"

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.new_doc", return_value=mock_msg_doc),
		):
			from frappe_ak.dispatcher.actions.send_whatsapp import execute
			execute(action, doc, auto)

		first_update = mock_msg_doc.update.call_args_list[0][0][0]
		self.assertEqual(first_update["to"], "+919876543210")

	def test_reference_doctype_and_name_set(self):
		"""WhatsApp Message doc should include triggering doc's doctype and name."""
		action = frappe._dict({
			"action_type": "Send WhatsApp",
			"wa_to": "+1234567890",
			"wa_message_body": "Hello",
			"wa_template_name": None,
		})
		doc = frappe._dict({"doctype": "Sales Order", "name": "SO-001"})
		auto = frappe._dict({"name": "AUTO-WA"})

		mock_msg_doc = MagicMock()
		mock_msg_doc.name = "WA-MSG-REF"

		with (
			patch("frappe.db.exists", return_value=True),
			patch("frappe.new_doc", return_value=mock_msg_doc),
		):
			from frappe_ak.dispatcher.actions.send_whatsapp import execute
			execute(action, doc, auto)

		first_update = mock_msg_doc.update.call_args_list[0][0][0]
		self.assertEqual(first_update["reference_doctype"], "Sales Order")
		self.assertEqual(first_update["reference_name"], "SO-001")
