"""Tests for www/shared.py — guest page context builder for Doc Designer."""

from unittest.mock import patch, MagicMock

import frappe
from frappe.tests import UnitTestCase
from frappe.utils import add_days, now_datetime

from frappe_ak.www.shared import get_context


class SharedPageTestMixin:
	"""Shared fixtures for guest page tests."""

	@classmethod
	def _create_template(cls, **kwargs):
		defaults = {
			"doctype": "AK Document Template",
			"template_name": f"Shared Page {frappe.generate_hash()[:6]}",
			"reference_doctype": "ToDo",
			"is_active": 1,
			"is_public_form": 0,
			"template_html": "<p>Hello {{ doc.name }}</p>",
			"lock_after_submission": 0,
			"disable_access_after_submission": 0,
			"expires_in_days": 7,
			"notify_on_view": 0,
			"track_opens": 0,
		}
		defaults.update(kwargs)
		return frappe.get_doc(defaults).insert(ignore_permissions=True)

	@classmethod
	def _create_todo(cls):
		return frappe.get_doc({
			"doctype": "ToDo", "description": "Shared page test",
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
		return frappe.get_doc(defaults).insert(ignore_permissions=True)


class TestSharedPageMissingKey(UnitTestCase):
	def test_missing_key_sets_error(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({})
		get_context(ctx)
		self.assertEqual(ctx.error_code, "missing_key")
		self.assertIn("No document key", ctx.error)


class TestSharedPageInvalidKey(UnitTestCase):
	def test_invalid_key_sets_error(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": "nonexistent-uuid-key"})
		get_context(ctx)
		self.assertEqual(ctx.error_code, "not_found")


class TestSharedPageExpired(UnitTestCase, SharedPageTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(template_name=f"Expired Page {frappe.generate_hash()[:6]}")
		cls.todo = cls._create_todo()
		cls.share = cls._create_share(cls.template.name, cls.todo.name)
		# Set expiry to yesterday
		frappe.db.set_value("AK Document Share", cls.share.name,
			"expires_at", add_days(now_datetime(), -1))
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Share", cls.share.name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_expired_share_sets_error(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertEqual(ctx.error_code, "expired")

	def test_expired_share_auto_deactivates(self):
		"""Viewing an expired share should auto-set is_active=0, status=Expired."""
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		share = frappe.db.get_value("AK Document Share", self.share.name,
			["is_active", "status"], as_dict=True)
		self.assertEqual(share.is_active, 0)
		self.assertEqual(share.status, "Expired")


class TestSharedPageInactive(UnitTestCase, SharedPageTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(template_name=f"Inactive Page {frappe.generate_hash()[:6]}")
		cls.todo = cls._create_todo()
		cls.share = cls._create_share(cls.template.name, cls.todo.name)
		frappe.db.set_value("AK Document Share", cls.share.name, "is_active", 0)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("AK Document Share", cls.share.name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_inactive_share_sets_error(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertEqual(ctx.error_code, "inactive")


class TestSharedPageLocked(UnitTestCase, SharedPageTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template_block = cls._create_template(
			template_name=f"Locked Block {frappe.generate_hash()[:6]}",
			disable_access_after_submission=1,
		)
		cls.template_allow = cls._create_template(
			template_name=f"Locked Allow {frappe.generate_hash()[:6]}",
			disable_access_after_submission=0,
		)
		cls.todo = cls._create_todo()
		cls.share_block = cls._create_share(cls.template_block.name, cls.todo.name)
		cls.share_allow = cls._create_share(cls.template_allow.name, cls.todo.name)
		frappe.db.set_value("AK Document Share", cls.share_block.name, "is_locked", 1)
		frappe.db.set_value("AK Document Share", cls.share_allow.name, "is_locked", 1)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		for s in [cls.share_block, cls.share_allow]:
			frappe.delete_doc("AK Document Share", s.name, ignore_permissions=True, force=True)
		for t in [cls.template_block, cls.template_allow]:
			frappe.delete_doc("AK Document Template", t.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_locked_with_disable_access(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share_block.secret_key})
		get_context(ctx)
		self.assertEqual(ctx.error_code, "submitted")

	def test_locked_without_disable_access(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share_allow.secret_key})
		get_context(ctx)
		# Should render normally but with is_locked=True
		self.assertTrue(ctx.is_locked)
		self.assertFalse(hasattr(ctx, "error_code") and ctx.error_code)


class TestSharedPageValid(UnitTestCase, SharedPageTestMixin):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.template = cls._create_template(template_name=f"Valid Page {frappe.generate_hash()[:6]}")
		cls.todo = cls._create_todo()
		cls.share = cls._create_share(cls.template.name, cls.todo.name)
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		# Clean up view logs
		for vl in frappe.get_all("AK Document View Log",
				filters={"document_share": cls.share.name}, pluck="name"):
			frappe.delete_doc("AK Document View Log", vl, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Share", cls.share.name, ignore_permissions=True, force=True)
		frappe.delete_doc("AK Document Template", cls.template.name, ignore_permissions=True, force=True)
		frappe.delete_doc("ToDo", cls.todo.name, ignore_permissions=True, force=True)
		frappe.db.commit()
		super().tearDownClass()

	def test_context_has_rendered_html(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertTrue(hasattr(ctx, "rendered_html"))
		self.assertIn("Hello", ctx.rendered_html)

	def test_context_has_secret_key(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertEqual(ctx.secret_key, self.share.secret_key)

	def test_context_has_title(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertEqual(ctx.title, self.template.template_name)

	def test_context_has_template_settings(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertIsNotNone(ctx.template_settings)

	def test_context_has_expiry_formatted(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertTrue(hasattr(ctx, "expires_at_formatted"))

	def test_no_error(self):
		ctx = frappe._dict()
		frappe.form_dict = frappe._dict({"key": self.share.secret_key})
		get_context(ctx)
		self.assertFalse(getattr(ctx, "error", None))
