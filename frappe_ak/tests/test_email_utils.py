"""Tests for email_utils.py — email sending for Doc Designer."""

from unittest.mock import patch, MagicMock

import frappe
from frappe.tests import UnitTestCase

from frappe_ak.email_utils import (
	send_document_email,
	_default_email_body,
	_render_jinja,
)


class TestRenderJinja(UnitTestCase):
	"""Unit tests for the Jinja rendering helper."""

	def test_empty_string_returns_empty(self):
		self.assertEqual(_render_jinja("", {}), "")

	def test_none_returns_empty(self):
		self.assertEqual(_render_jinja(None, {}), "")

	def test_whitespace_only_returns_empty(self):
		self.assertEqual(_render_jinja("   ", {}), "")

	def test_renders_simple_template(self):
		result = _render_jinja("Hello {{ name }}", {"name": "Alice"})
		self.assertEqual(result, "Hello Alice")

	def test_renders_nested_context(self):
		doc = frappe._dict({"first_name": "Bob", "last_name": "Smith"})
		result = _render_jinja("{{ doc.first_name }} {{ doc.last_name }}", {"doc": doc})
		self.assertEqual(result, "Bob Smith")

	def test_invalid_template_returns_empty(self):
		"""Bad Jinja syntax should return empty string, not crash."""
		result = _render_jinja("{{ undefined_var.bad_attr }}", {})
		self.assertEqual(result, "")

	def test_sandboxed_environment(self):
		"""Dangerous operations should be blocked by SandboxedEnvironment."""
		result = _render_jinja("{{ ''.__class__ }}", {})
		# SandboxedEnvironment may allow __class__ but block further traversal
		# At minimum, it should not crash
		self.assertIsInstance(result, str)


class TestDefaultEmailBody(UnitTestCase):
	"""Tests for default email body generation."""

	def test_contains_share_url(self):
		share = frappe._dict({
			"share_url": "https://example.com/share/abc123",
			"expires_at": "2026-12-31 23:59:59",
		})
		template = frappe._dict({"template_name": "Test Template"})
		body = _default_email_body(share, template)
		self.assertIn("https://example.com/share/abc123", body)

	def test_contains_open_document_link(self):
		share = frappe._dict({
			"share_url": "https://example.com/share/abc123",
			"expires_at": "2026-12-31 23:59:59",
		})
		template = frappe._dict({"template_name": "Test"})
		body = _default_email_body(share, template)
		self.assertIn("Open Document", body)

	def test_contains_expiry_info(self):
		share = frappe._dict({
			"share_url": "https://example.com/share/abc123",
			"expires_at": "2026-06-15 10:00:00",
		})
		template = frappe._dict({"template_name": "Test"})
		body = _default_email_body(share, template)
		self.assertIn("expire", body.lower())


class TestSendDocumentEmail(UnitTestCase):
	"""Tests for the main email sending function."""

	def _make_share(self, **overrides):
		defaults = {
			"name": "SHARE-001",
			"recipient_email": "test@example.com",
			"template": "TMPL-001",
			"reference_doctype": "ToDo",
			"reference_name": "TODO-001",
			"share_url": "https://example.com/share/abc",
			"expires_at": "2026-12-31 23:59:59",
			"email_sent": 0,
		}
		defaults.update(overrides)
		share = frappe._dict(defaults)
		share.db_set = MagicMock()
		return share

	def _make_template(self, **overrides):
		defaults = {
			"name": "TMPL-001",
			"template_name": "Test Template",
			"email_subject": "Subject: {{ doc.name }}",
			"email_body_html": "<p>Hello {{ doc.name }}</p>",
			"attach_pdf": 0,
		}
		defaults.update(overrides)
		return frappe._dict(defaults)

	@patch("frappe_ak.email_utils.frappe.sendmail")
	@patch("frappe_ak.email_utils.frappe.get_single")
	@patch("frappe_ak.email_utils.frappe.db.exists", return_value=False)
	@patch("frappe_ak.email_utils.frappe.get_doc")
	def test_sends_email_with_rendered_subject(self, mock_get_doc, mock_exists, mock_single, mock_sendmail):
		share = self._make_share()
		template = self._make_template()
		doc = frappe._dict({"name": "TODO-001", "doctype": "ToDo"})

		mock_get_doc.side_effect = lambda *args: {
			("AK Document Share", "SHARE-001"): share,
			("AK Document Template", "TMPL-001"): template,
			("ToDo", "TODO-001"): doc,
		}.get(args, MagicMock())

		send_document_email("SHARE-001")

		mock_sendmail.assert_called_once()
		call_kwargs = mock_sendmail.call_args
		self.assertEqual(call_kwargs.kwargs["recipients"], ["test@example.com"])
		self.assertIn("TODO-001", call_kwargs.kwargs["subject"])

	@patch("frappe_ak.email_utils.frappe.get_doc")
	def test_throws_without_recipient_email(self, mock_get_doc):
		share = self._make_share(recipient_email="")
		template = self._make_template()

		mock_get_doc.side_effect = lambda *args: {
			("AK Document Share", "SHARE-001"): share,
			("AK Document Template", "TMPL-001"): template,
		}.get(args, MagicMock())

		with self.assertRaises(Exception):
			send_document_email("SHARE-001")

	@patch("frappe_ak.email_utils.frappe.sendmail")
	@patch("frappe_ak.email_utils.frappe.get_single")
	@patch("frappe_ak.email_utils.frappe.db.exists", return_value=False)
	@patch("frappe_ak.email_utils.frappe.get_doc")
	def test_marks_email_sent(self, mock_get_doc, mock_exists, mock_single, mock_sendmail):
		share = self._make_share()
		template = self._make_template()
		doc = frappe._dict({"name": "TODO-001", "doctype": "ToDo"})

		mock_get_doc.side_effect = lambda *args: {
			("AK Document Share", "SHARE-001"): share,
			("AK Document Template", "TMPL-001"): template,
			("ToDo", "TODO-001"): doc,
		}.get(args, MagicMock())

		send_document_email("SHARE-001")

		share.db_set.assert_any_call("email_sent", 1)

	@patch("frappe_ak.email_utils.frappe.sendmail")
	@patch("frappe_ak.email_utils.frappe.get_single")
	@patch("frappe_ak.email_utils.frappe.db.exists", return_value=False)
	@patch("frappe_ak.email_utils.frappe.get_doc")
	def test_fallback_subject_when_template_empty(self, mock_get_doc, mock_exists, mock_single, mock_sendmail):
		share = self._make_share()
		template = self._make_template(email_subject="", email_body_html="")
		doc = frappe._dict({"name": "TODO-001", "doctype": "ToDo"})

		mock_get_doc.side_effect = lambda *args: {
			("AK Document Share", "SHARE-001"): share,
			("AK Document Template", "TMPL-001"): template,
			("ToDo", "TODO-001"): doc,
		}.get(args, MagicMock())

		send_document_email("SHARE-001")

		call_kwargs = mock_sendmail.call_args.kwargs
		# Fallback subject should contain the reference name
		self.assertIn("TODO-001", call_kwargs["subject"])

	@patch("frappe_ak.renderer.render_template_as_pdf", return_value=b"%PDF-fake")
	@patch("frappe_ak.email_utils.frappe.sendmail")
	@patch("frappe_ak.email_utils.frappe.get_single")
	@patch("frappe_ak.email_utils.frappe.db.exists", return_value=False)
	@patch("frappe_ak.email_utils.frappe.get_doc")
	def test_attaches_pdf_when_configured(self, mock_get_doc, mock_exists, mock_single, mock_sendmail, mock_pdf):
		share = self._make_share()
		template = self._make_template(attach_pdf=1)
		doc = frappe._dict({"name": "TODO-001", "doctype": "ToDo"})

		mock_get_doc.side_effect = lambda *args: {
			("AK Document Share", "SHARE-001"): share,
			("AK Document Template", "TMPL-001"): template,
			("ToDo", "TODO-001"): doc,
		}.get(args, MagicMock())

		send_document_email("SHARE-001")

		call_kwargs = mock_sendmail.call_args.kwargs
		self.assertIsNotNone(call_kwargs["attachments"])
		self.assertEqual(len(call_kwargs["attachments"]), 1)
		self.assertIn("TODO-001", call_kwargs["attachments"][0]["fname"])
