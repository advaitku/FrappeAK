"""Tests for AK Document Share and AK Document Template DocType controllers."""

import json
import uuid
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import add_days, now_datetime, getdate, get_url


# ---------------------------------------------------------------------------
# AK Document Template — validate()
# ---------------------------------------------------------------------------
class TestAKDocumentTemplateValidate(UnitTestCase):
	def _make_template(self, **kwargs):
		defaults = {
			"doctype": "AK Document Template",
			"template_name": f"Validate Test {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"is_public_form": 0,
			"template_html": "<p>Test</p>",
			"expires_in_days": 7,
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults)

	def test_template_html_required(self):
		doc = self._make_template(template_html="", is_public_form=0)
		with self.assertRaises(Exception) as ctx:
			doc.insert(ignore_permissions=True)
		self.assertIn("Template HTML is required", str(ctx.exception))

	def test_template_html_not_required_for_public_form(self):
		doc = self._make_template(template_html="", is_public_form=1)
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		frappe.delete_doc("AK Document Template", doc.name, ignore_permissions=True, force=True)

	def test_auto_send_requires_field(self):
		doc = self._make_template(auto_send_on="on_insert", auto_send_to_field="")
		with self.assertRaises(Exception) as ctx:
			doc.insert(ignore_permissions=True)
		self.assertIn("Auto Send To Field is required", str(ctx.exception))

	def test_expires_in_days_minimum(self):
		doc = self._make_template(expires_in_days=-1)
		with self.assertRaises(Exception) as ctx:
			doc.insert(ignore_permissions=True)
		self.assertIn("at least 1", str(ctx.exception))

	def test_valid_template_saves(self):
		doc = self._make_template()
		doc.insert(ignore_permissions=True)
		self.assertTrue(doc.name)
		frappe.delete_doc("AK Document Template", doc.name, ignore_permissions=True, force=True)

	def test_on_update_clears_cache(self):
		doc = self._make_template()
		doc.insert(ignore_permissions=True)
		frappe.db.commit()
		with patch.object(frappe.cache, "delete_value") as mock_del:
			doc.template_html = "<p>Updated</p>"
			doc.save(ignore_permissions=True)
			mock_del.assert_any_call(f"ak_template_{doc.name}")
		frappe.delete_doc("AK Document Template", doc.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# AK Document Share — before_insert()
# ---------------------------------------------------------------------------
class TestAKDocumentShareBeforeInsert(UnitTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = frappe.get_doc({
			"doctype": "AK Document Template",
			"template_name": f"Share Insert Test {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"template_html": "<p>Test</p>",
			"expires_in_days": 10,
		}).insert(ignore_permissions=True)
		cls.todo = frappe.get_doc({
			"doctype": "ToDo", "description": "Share insert test",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def _create_and_cleanup(self, **kwargs):
		defaults = {
			"doctype": "AK Document Share",
			"template": self.template.name,
			"reference_doctype": "ToDo",
			"reference_name": self.todo.name,
		}
		defaults.update(kwargs)
		doc = frappe.get_doc(defaults).insert(ignore_permissions=True)
		frappe.db.commit()
		return doc

	def test_secret_key_auto_generated(self):
		doc = self._create_and_cleanup()
		self.assertIsNotNone(doc.secret_key)
		# Should be a valid UUID
		uuid.UUID(doc.secret_key)
		frappe.delete_doc("AK Document Share", doc.name, ignore_permissions=True, force=True)

	def test_shared_by_auto_set(self):
		doc = self._create_and_cleanup()
		self.assertEqual(doc.shared_by, frappe.session.user)
		frappe.delete_doc("AK Document Share", doc.name, ignore_permissions=True, force=True)

	def test_reference_doctype_from_template(self):
		"""Verify before_insert auto-fills reference_doctype from the template."""
		doc = frappe.get_doc({
			"doctype": "AK Document Share",
			"template": self.template.name,
			"reference_doctype": "ToDo",
			"reference_name": self.todo.name,
		})
		# Clear reference_doctype to simulate omission, then call before_insert
		doc.reference_doctype = None
		doc.before_insert()
		self.assertEqual(doc.reference_doctype, "ToDo")

	def test_expires_at_from_template(self):
		doc = self._create_and_cleanup()
		self.assertIsNotNone(doc.expires_at)
		from frappe.utils import date_diff
		days = date_diff(getdate(doc.expires_at), getdate(now_datetime()))
		# Template has expires_in_days=10
		self.assertGreaterEqual(days, 9)
		self.assertLessEqual(days, 11)
		frappe.delete_doc("AK Document Share", doc.name, ignore_permissions=True, force=True)

	def test_share_url_format(self):
		doc = self._create_and_cleanup()
		expected_url = f"{get_url()}/shared?key={doc.secret_key}"
		self.assertEqual(doc.share_url, expected_url)
		frappe.delete_doc("AK Document Share", doc.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# AK Document Share — validate()
# ---------------------------------------------------------------------------
class TestAKDocumentShareValidate(UnitTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = frappe.get_doc({
			"doctype": "AK Document Template",
			"template_name": f"Share Validate Test {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"template_html": "<p>Test</p>",
			"expires_in_days": 7,
		}).insert(ignore_permissions=True)
		cls.todo = frappe.get_doc({
			"doctype": "ToDo", "description": "Share validate test",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_template_required(self):
		with self.assertRaises(Exception):
			frappe.get_doc({
				"doctype": "AK Document Share",
				"reference_doctype": "ToDo",
				"reference_name": self.todo.name,
			}).insert(ignore_permissions=True)

	def test_reference_name_required_for_non_public(self):
		with self.assertRaises(Exception) as ctx:
			frappe.get_doc({
				"doctype": "AK Document Share",
				"template": self.template.name,
				"reference_doctype": "ToDo",
				# Missing reference_name
			}).insert(ignore_permissions=True)
		self.assertIn("Reference Name is required", str(ctx.exception))

	def test_past_expiry_rejected(self):
		with self.assertRaises(Exception) as ctx:
			frappe.get_doc({
				"doctype": "AK Document Share",
				"template": self.template.name,
				"reference_doctype": "ToDo",
				"reference_name": self.todo.name,
				"expires_at": add_days(now_datetime(), -5),
			}).insert(ignore_permissions=True)
		self.assertIn("future", str(ctx.exception))


# ---------------------------------------------------------------------------
# AK Document Share — log_view()
# ---------------------------------------------------------------------------
class TestAKDocumentShareLogView(UnitTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = frappe.get_doc({
			"doctype": "AK Document Template",
			"template_name": f"Log View Test {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"template_html": "<p>Test</p>",
			"expires_in_days": 7,
			"track_opens": 1,
		}).insert(ignore_permissions=True)
		cls.todo = frappe.get_doc({
			"doctype": "ToDo", "description": "Log view test",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	def setUp(self):
		# log_view() accesses frappe.local.request and request_ip
		# which may not exist in test context
		if not hasattr(frappe.local, "request") or frappe.local.request is None:
			frappe.local.request = None
		if not hasattr(frappe.local, "request_ip"):
			frappe.local.request_ip = None

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_view_count_increments(self):
		share = frappe.get_doc({
			"doctype": "AK Document Share",
			"template": self.template.name,
			"reference_doctype": "ToDo",
			"reference_name": self.todo.name,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		self.assertEqual(share.view_count, 0)
		share.log_view()
		share.reload()
		self.assertEqual(share.view_count, 1)
		share.log_view()
		share.reload()
		self.assertEqual(share.view_count, 2)

		# Cleanup view logs
		for vl in frappe.get_all("AK Document View Log",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document View Log", vl, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_status_active_to_viewed(self):
		share = frappe.get_doc({
			"doctype": "AK Document Share",
			"template": self.template.name,
			"reference_doctype": "ToDo",
			"reference_name": self.todo.name,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		self.assertEqual(share.status, "Active")
		share.log_view()
		share.reload()
		self.assertEqual(share.status, "Viewed")

		for vl in frappe.get_all("AK Document View Log",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document View Log", vl, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)

	def test_view_log_created_when_tracking(self):
		share = frappe.get_doc({
			"doctype": "AK Document Share",
			"template": self.template.name,
			"reference_doctype": "ToDo",
			"reference_name": self.todo.name,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		share.log_view()
		logs = frappe.get_all("AK Document View Log",
			filters={"document_share": share.name})
		self.assertEqual(len(logs), 1)

		for vl in logs:
			frappe.delete_doc("AK Document View Log", vl.name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# AK Document Share — revoke()
# ---------------------------------------------------------------------------
class TestAKDocumentShareRevoke(UnitTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = frappe.get_doc({
			"doctype": "AK Document Template",
			"template_name": f"Revoke Test {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"template_html": "<p>Test</p>",
			"expires_in_days": 7,
		}).insert(ignore_permissions=True)
		cls.todo = frappe.get_doc({
			"doctype": "ToDo", "description": "Revoke test",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_revoke_deactivates_share(self):
		share = frappe.get_doc({
			"doctype": "AK Document Share",
			"template": self.template.name,
			"reference_doctype": "ToDo",
			"reference_name": self.todo.name,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		self.assertEqual(share.is_active, 1)
		share.revoke()
		share.reload()
		self.assertEqual(share.is_active, 0)
		self.assertEqual(share.status, "Expired")

		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)


# ---------------------------------------------------------------------------
# Full Lifecycle Integration Test
# ---------------------------------------------------------------------------
class TestFullLifecycle(UnitTestCase):
	"""End-to-end: create template → create share → view → submit → verify lock."""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = frappe.get_doc({
			"doctype": "AK Document Template",
			"template_name": f"Lifecycle Test {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"template_html": "<p>{{ doc.description }}</p>{{ ak_submit_button() }}",
			"lock_after_submission": 1,
			"disable_access_after_submission": 0,
			"expires_in_days": 7,
			"track_opens": 1,
			"notify_on_view": 0,
			"success_message": "Lifecycle complete!",
			"fields": [
				{"field_name": "description", "field_label": "Description",
				 "field_type": "Data", "is_editable": 1, "is_mandatory": 0,
				 "is_existing_field": 1},
			],
		}).insert(ignore_permissions=True)
		cls.todo = frappe.get_doc({
			"doctype": "ToDo", "description": "Original description",
		}).insert(ignore_permissions=True)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def setUp(self):
		# log_view() accesses frappe.local.request and request_ip
		if not hasattr(frappe.local, "request") or frappe.local.request is None:
			frappe.local.request = None
		if not hasattr(frappe.local, "request_ip"):
			frappe.local.request_ip = None

	def test_full_lifecycle(self):
		# 1. Create share
		share = frappe.get_doc({
			"doctype": "AK Document Share",
			"template": self.template.name,
			"reference_doctype": "ToDo",
			"reference_name": self.todo.name,
		}).insert(ignore_permissions=True)
		frappe.db.commit()

		self.assertEqual(share.status, "Active")
		self.assertEqual(share.is_active, 1)
		self.assertIsNotNone(share.secret_key)

		# 2. Log view
		share.log_view()
		share.reload()
		self.assertEqual(share.view_count, 1)
		self.assertEqual(share.status, "Viewed")

		# 3. Submit response
		from frappe_ak.doc_api import submit_response
		result = submit_response(
			share.secret_key, "Submitted",
			json.dumps({"description": "Updated by recipient"}),
		)
		self.assertTrue(result["success"])
		self.assertEqual(result["message"], "Lifecycle complete!")

		# 4. Verify share is locked (use db.get_value — reload() can return
		#    stale cached values after db.set_value in submit_response)
		share_vals = frappe.db.get_value(
			"AK Document Share", share.name,
			["is_locked", "status"], as_dict=True,
		)
		self.assertEqual(share_vals.is_locked, 1)
		self.assertEqual(share_vals.status, "Submitted")

		# 5. Verify response record exists
		responses = frappe.get_all("AK Document Response",
			filters={"document_share": share.name},
			fields=["name", "response_type", "response_data"])
		self.assertEqual(len(responses), 1)
		self.assertEqual(responses[0].response_type, "Submitted")
		data = json.loads(responses[0].response_data)
		self.assertEqual(data["description"], "Updated by recipient")

		# 6. Verify original doc was updated
		self.todo.reload()
		self.assertEqual(self.todo.description, "Updated by recipient")

		# 7. Attempting another submission should fail (locked)
		with self.assertRaises(Exception) as ctx:
			submit_response(share.secret_key, "Submitted",
				json.dumps({"description": "Second attempt"}))
		self.assertIn("already been submitted", str(ctx.exception))

		# Restore original doc
		self.todo.description = "Original description"
		self.todo.save(ignore_permissions=True)

		# Cleanup
		for r in responses:
			frappe.delete_doc("AK Document Response", r.name, ignore_permissions=True, force=True)
		for vl in frappe.get_all("AK Document View Log",
				filters={"document_share": share.name}, pluck="name"):
			frappe.delete_doc("AK Document View Log", vl, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", share.name, ignore_permissions=True, force=True)
