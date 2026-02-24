"""Tests for doc_api.py — all whitelisted API endpoints for Doc Designer."""

import json
from unittest.mock import patch, MagicMock

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import add_days, now_datetime, nowdate

from frappe_ak.doc_api import (
	submit_response,
	create_share,
	download_pdf,
	get_doctype_fields,
	notify_on_view,
	check_auto_send,
	preview_template,
	render_response as api_render_response,
)


class DocDesignerTestMixin:
	"""Shared fixtures for Doc Designer API tests."""

	@classmethod
	def _create_template(cls, **kwargs):
		fields = kwargs.pop("fields", [])
		response_actions = kwargs.pop("response_actions", [])
		defaults = {
			"doctype": "AK Document Template",
			"template_name": f"Test API {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"is_public_form": 0,
			"template_html": "<p>Hello {{ doc.name }}</p>{{ ak_submit_button() }}",
			"lock_after_submission": 1,
			"disable_access_after_submission": 0,
			"expires_in_days": 7,
			"success_message": "Thank you!",
			"attach_pdf_on_submission": 0,
			"notify_on_response": 0,
			"notify_on_view": 0,
			"track_opens": 0,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		for f in fields:
			doc.append("fields", f)
		for a in response_actions:
			doc.append("response_actions", a)
		doc.insert(ignore_permissions=True)
		return doc

	@classmethod
	def _create_todo(cls, description="Test todo"):
		return frappe.get_doc({
			"doctype": "ToDo",
			"description": description,
		}).insert(ignore_permissions=True)

	@classmethod
	def _create_share(cls, template_name, reference_name, **kwargs):
		defaults = {
			"doctype": "AK Document Share",
			"template": template_name,
			"reference_doctype": "ToDo",
			"reference_name": reference_name,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults)
		doc.insert(ignore_permissions=True)
		return doc


# ---------------------------------------------------------------------------
# submit_response()
# ---------------------------------------------------------------------------
class TestSubmitResponse(UnitTestCase, DocDesignerTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(
			fields=[
				{"field_name": "approver_name", "field_label": "Approver Name",
				 "field_type": "Data", "is_editable": 1, "is_mandatory": 1,
				 "is_existing_field": 0},
				{"field_name": "notes", "field_label": "Notes",
				 "field_type": "Text", "is_editable": 1, "is_mandatory": 0,
				 "is_existing_field": 0},
				{"field_name": "description", "field_label": "Description",
				 "field_type": "Data", "is_editable": 1, "is_mandatory": 0,
				 "is_existing_field": 1},
			],
		)
		cls.todo = cls._create_todo("Submit response test")
		cls.share = cls._create_share(cls.template.name, cls.todo.name)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		# Clean up responses
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": cls.share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", cls.share.name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def _fresh_share(self):
		"""Create a fresh share for each test that mutates state."""
		share = self._create_share(self.template.name, self.todo.name)
		frappe.db.commit()
		return share

	def test_valid_submission(self):
		share = self._fresh_share()
		result = submit_response(
			share.secret_key, "Submitted",
			json.dumps({"approver_name": "Alice", "notes": "OK"}),
		)
		self.assertTrue(result["success"])
		self.assertEqual(result["message"], "Thank you!")
		# Cleanup
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_invalid_secret_key(self):
		with self.assertRaises(frappe.DoesNotExistError):
			submit_response("nonexistent-key", "Submitted", "{}")

	def test_inactive_share(self):
		share = self._fresh_share()
		frappe.db.set_value("AK Document Share", share.name, "is_active", 0)
		frappe.db.commit()
		with self.assertRaises(Exception) as ctx:
			submit_response(share.secret_key, "Submitted",
				json.dumps({"approver_name": "Test"}))
		self.assertIn("no longer active", str(ctx.exception))
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_locked_share(self):
		share = self._fresh_share()
		frappe.db.set_value("AK Document Share", share.name, "is_locked", 1)
		frappe.db.commit()
		with self.assertRaises(Exception) as ctx:
			submit_response(share.secret_key, "Submitted",
				json.dumps({"approver_name": "Test"}))
		self.assertIn("already been submitted", str(ctx.exception))
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_expired_share(self):
		share = self._fresh_share()
		frappe.db.set_value("AK Document Share", share.name,
			"expires_at", add_days(now_datetime(), -1))
		frappe.db.commit()
		with self.assertRaises(Exception) as ctx:
			submit_response(share.secret_key, "Submitted",
				json.dumps({"approver_name": "Test"}))
		self.assertIn("expired", str(ctx.exception))
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_mandatory_field_validation(self):
		share = self._fresh_share()
		with self.assertRaises(Exception) as ctx:
			submit_response(share.secret_key, "Submitted",
				json.dumps({"notes": "missing approver_name"}))
		self.assertIn("mandatory", str(ctx.exception))
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_share_locked_after_submission(self):
		share = self._fresh_share()
		submit_response(share.secret_key, "Submitted",
			json.dumps({"approver_name": "Alice"}))
		share_after = frappe.db.get_value("AK Document Share", share.name,
			["is_locked", "status"], as_dict=True)
		self.assertEqual(share_after.is_locked, 1)
		self.assertEqual(share_after.status, "Submitted")
		# Cleanup
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_response_record_created(self):
		share = self._fresh_share()
		submit_response(share.secret_key, "Accepted",
			json.dumps({"approver_name": "Bob"}))
		responses = frappe.get_all("AK Document Response",
			filters={"document_share": share.name},
			fields=["name", "response_type", "response_data"])
		self.assertTrue(len(responses) > 0)
		self.assertEqual(responses[0].response_type, "Accepted")
		data = json.loads(responses[0].response_data)
		self.assertEqual(data["approver_name"], "Bob")
		# Cleanup
		for r in responses:
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_existing_field_updates_doc(self):
		"""Editable existing fields should update the original document."""
		share = self._fresh_share()
		submit_response(share.secret_key, "Submitted",
			json.dumps({"approver_name": "Alice", "description": "Updated description"}))
		todo = frappe.get_doc("ToDo", self.todo.name)
		self.assertEqual(todo.description, "Updated description")
		# Restore original
		todo.description = "Submit response test"
		todo.save(ignore_permissions=True)
		# Cleanup
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_share_status_accepted(self):
		share = self._fresh_share()
		submit_response(share.secret_key, "Accepted",
			json.dumps({"approver_name": "X"}))
		status = frappe.db.get_value("AK Document Share", share.name, "status")
		self.assertEqual(status, "Accepted")
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_share_status_declined(self):
		share = self._fresh_share()
		submit_response(share.secret_key, "Declined",
			json.dumps({"approver_name": "X"}))
		status = frappe.db.get_value("AK Document Share", share.name, "status")
		self.assertEqual(status, "Declined")
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# submit_response() — Response Actions
# ---------------------------------------------------------------------------
class TestSubmitResponseActions(UnitTestCase, DocDesignerTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(
			template_name=f"Action {frappe.generate_hash()[:6]}",
			lock_after_submission=0,
			response_actions=[
				{"response_type": "Accepted", "field_name": "status", "value": "Closed"},
				{"response_type": "Declined", "field_name": "status", "value": "Cancelled"},
			],
		)
		cls.todo = cls._create_todo("Response action test")
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_accept_action_updates_field(self):
		share = self._create_share(self.template.name, self.todo.name)
		frappe.db.commit()
		submit_response(share.secret_key, "Accepted", "{}")
		status = frappe.db.get_value("ToDo", self.todo.name, "status")
		self.assertEqual(status, "Closed")
		# Restore
		frappe.db.set_value("ToDo", self.todo.name, "status", "Open")
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_decline_action_updates_field(self):
		share = self._create_share(self.template.name, self.todo.name)
		frappe.db.commit()
		submit_response(share.secret_key, "Declined", "{}")
		status = frappe.db.get_value("ToDo", self.todo.name, "status")
		self.assertEqual(status, "Cancelled")
		# Restore
		frappe.db.set_value("ToDo", self.todo.name, "status", "Open")
		for r in frappe.get_all("AK Document Response",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document Response", r, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# create_share()
# ---------------------------------------------------------------------------
class TestCreateShare(UnitTestCase, DocDesignerTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(template_name=f"Share Test {frappe.generate_hash()[:6]}")
		cls.todo = cls._create_todo("Share creation test")
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def _cleanup_share(self, name):
		frappe.delete_doc("AK Document Share", name, ignore_permissions=True, force=True)

	def test_creates_share_with_url(self):
		result = create_share(self.template.name, "ToDo", self.todo.name)
		self.assertIn("name", result)
		self.assertIn("share_url", result)
		self.assertIn("secret_key", result)
		self.assertIn("/shared?key=", result["share_url"])
		self._cleanup_share(result["name"])

	def test_secret_key_is_uuid(self):
		result = create_share(self.template.name, "ToDo", self.todo.name)
		# UUID format: 8-4-4-4-12
		self.assertEqual(len(result["secret_key"].split("-")), 5)
		self._cleanup_share(result["name"])

	def test_default_expiry_from_template(self):
		result = create_share(self.template.name, "ToDo", self.todo.name)
		self.assertIn("expires_at", result)
		self.assertNotEqual(result["expires_at"], "None")
		self._cleanup_share(result["name"])

	def test_custom_expiry(self):
		result = create_share(self.template.name, "ToDo", self.todo.name,
			expires_in_days=30)
		share = frappe.get_doc("AK Document Share", result["name"])
		# Should be ~30 days from now
		from frappe.utils import date_diff, getdate
		days = date_diff(getdate(share.expires_at), getdate(nowdate()))
		self.assertGreaterEqual(days, 29)
		self.assertLessEqual(days, 31)
		self._cleanup_share(result["name"])

	def test_recipient_email(self):
		result = create_share(self.template.name, "ToDo", self.todo.name,
			recipient_email="test@example.com")
		share = frappe.get_doc("AK Document Share", result["name"])
		self.assertEqual(share.recipient_email, "test@example.com")
		self._cleanup_share(result["name"])


# ---------------------------------------------------------------------------
# download_pdf()
# ---------------------------------------------------------------------------
class TestDownloadPDF(UnitTestCase, DocDesignerTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(template_name=f"PDF Test {frappe.generate_hash()[:6]}")
		cls.todo = cls._create_todo("PDF download test")
		cls.share = cls._create_share(cls.template.name, cls.todo.name)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Share", cls.share.name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_invalid_key_throws(self):
		with self.assertRaises(frappe.DoesNotExistError):
			download_pdf("bad-key")

	def test_inactive_share_throws(self):
		share = self._create_share(self.template.name, self.todo.name)
		frappe.db.set_value("AK Document Share", share.name, "is_active", 0)
		frappe.db.commit()
		with self.assertRaises(Exception) as ctx:
			download_pdf(share.secret_key)
		self.assertIn("no longer active", str(ctx.exception))
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_expired_share_throws(self):
		share = self._create_share(self.template.name, self.todo.name)
		frappe.db.set_value("AK Document Share", share.name,
			"expires_at", add_days(now_datetime(), -1))
		frappe.db.commit()
		with self.assertRaises(Exception) as ctx:
			download_pdf(share.secret_key)
		self.assertIn("expired", str(ctx.exception))
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# get_doctype_fields()
# ---------------------------------------------------------------------------
class TestGetDoctypeFields(UnitTestCase):
	def test_returns_fields_and_child_tables(self):
		result = get_doctype_fields("ToDo")
		self.assertIn("fields", result)
		self.assertIn("child_tables", result)
		self.assertIsInstance(result["fields"], list)
		self.assertIsInstance(result["child_tables"], dict)

	def test_fields_have_expected_keys(self):
		result = get_doctype_fields("ToDo")
		for f in result["fields"]:
			self.assertIn("fieldname", f)
			self.assertIn("label", f)
			self.assertIn("fieldtype", f)

	def test_excludes_layout_fields(self):
		result = get_doctype_fields("ToDo")
		fieldtypes = [f["fieldtype"] for f in result["fields"]]
		for excluded in ("Section Break", "Column Break", "Tab Break"):
			self.assertNotIn(excluded, fieldtypes)

	def test_includes_table_fields(self):
		"""Table fields should be in child_tables, not main fields."""
		result = get_doctype_fields("ToDo")
		# Table fields should have is_child_table=1 in fields list
		table_fields = [f for f in result["fields"] if f.get("is_child_table")]
		# child_tables dict should have entries for each Table field
		for f in table_fields:
			self.assertIn(f["fieldname"], result["child_tables"])


# ---------------------------------------------------------------------------
# notify_on_view()
# ---------------------------------------------------------------------------
class TestNotifyOnView(UnitTestCase, DocDesignerTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(
			template_name=f"View Notify {frappe.generate_hash()[:6]}",
			notify_on_view=1,
		)
		cls.todo = cls._create_todo("View notify test")
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_notifies_on_first_view(self):
		share = self._create_share(self.template.name, self.todo.name)
		# Set view_count to 1 (first view just happened)
		frappe.db.set_value("AK Document Share", share.name, "view_count", 1)
		frappe.db.commit()

		with (
			patch("frappe.publish_realtime") as mock_rt,
			patch("frappe.sendmail") as mock_mail,
		):
			notify_on_view(share.name)
			# Should attempt notification
			mock_rt.assert_called_once()

		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_skips_subsequent_views(self):
		share = self._create_share(self.template.name, self.todo.name)
		frappe.db.set_value("AK Document Share", share.name, "view_count", 5)
		frappe.db.commit()

		with (
			patch("frappe.publish_realtime") as mock_rt,
			patch("frappe.sendmail") as mock_mail,
		):
			notify_on_view(share.name)
			mock_rt.assert_not_called()
			mock_mail.assert_not_called()

		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_skips_when_flag_off(self):
		template_no_notify = self._create_template(
			template_name=f"No Notify {frappe.generate_hash()[:6]}",
			notify_on_view=0,
		)
		share = self._create_share(template_no_notify.name, self.todo.name)
		frappe.db.set_value("AK Document Share", share.name, "view_count", 1)
		frappe.db.commit()

		with (
			patch("frappe.publish_realtime") as mock_rt,
			patch("frappe.sendmail") as mock_mail,
		):
			notify_on_view(share.name)
			mock_rt.assert_not_called()
			mock_mail.assert_not_called()

		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Template", template_no_notify.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# check_auto_send()
# ---------------------------------------------------------------------------
class TestCheckAutoSend(UnitTestCase, DocDesignerTestMixin):
	def test_skips_unknown_event(self):
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1"})
		with patch("frappe.get_all", return_value=[]) as mock_get:
			check_auto_send(doc, "on_trash")
			mock_get.assert_not_called()

	def test_skips_if_no_recipient(self):
		doc = frappe._dict({"doctype": "ToDo", "name": "T-1", "owner": ""})
		templates = [frappe._dict({
			"name": "TMPL-1", "auto_send_to_field": "owner", "expires_in_days": 7,
		})]
		with (
			patch("frappe.get_all", return_value=templates),
			patch("frappe_ak.doc_api.create_share") as mock_create,
		):
			check_auto_send(doc, "after_insert")
			mock_create.assert_not_called()

	def test_triggers_on_matching_event(self):
		doc = frappe._dict({
			"doctype": "ToDo", "name": "T-1", "assigned_by": "test@example.com",
		})
		templates = [frappe._dict({
			"name": "TMPL-1", "auto_send_to_field": "assigned_by", "expires_in_days": 7,
		})]
		with (
			patch("frappe.get_all", return_value=templates),
			patch("frappe_ak.doc_api.create_share", return_value={"name": "AK-DS-999"}) as mock_create,
			patch("frappe_ak.doc_api.send_document_email") as mock_send,
		):
			check_auto_send(doc, "after_insert")
			mock_create.assert_called_once()
			mock_send.assert_called_once_with("AK-DS-999")


# ---------------------------------------------------------------------------
# preview_template()
# ---------------------------------------------------------------------------
class TestPreviewTemplate(UnitTestCase, DocDesignerTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(
			template_name=f"Preview {frappe.generate_hash()[:6]}",
			template_html="<p>Preview: {{ doc.description }}</p>",
		)
		cls.todo = cls._create_todo("Preview test doc")
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_renders_with_doc_data(self):
		result = preview_template(self.template.name, self.todo.name)
		self.assertIn("html", result)
		self.assertIn("Preview test doc", result["html"])

	def test_renders_without_doc(self):
		result = preview_template(self.template.name)
		self.assertIn("html", result)
		# Should not crash — doc is empty _dict

	def test_template_error_handled(self):
		bad_template = self._create_template(
			template_name=f"Bad Preview {frappe.generate_hash()[:6]}",
			template_html="{{ undefined_var.bad_attr }}",
		)
		frappe.db.commit()
		result = preview_template(bad_template.name)
		self.assertIn("html", result)
		self.assertIn("Error", result["html"])
		frappe.delete_doc("AK Document Template", bad_template.name, ignore_permissions=True, force=True)

	def test_returns_custom_css(self):
		css_template = self._create_template(
			template_name=f"CSS Preview {frappe.generate_hash()[:6]}",
			template_html="<p>X</p>",
			custom_css=".custom { color: red; }",
		)
		frappe.db.commit()
		result = preview_template(css_template.name)
		self.assertEqual(result["css"], ".custom { color: red; }")
		frappe.delete_doc("AK Document Template", css_template.name, ignore_permissions=True, force=True)
