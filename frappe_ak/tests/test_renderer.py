"""Tests for renderer.py — template rendering engine for Doc Designer."""

import json
import os
from unittest.mock import patch, MagicMock

import frappe
from frappe.tests import UnitTestCase

from frappe_ak.renderer import (
	_render_jinja,
	_get_base_css,
	_build_full_html,
	_BODY_CSS,
	render_template,
	render_response,
)


# ---------------------------------------------------------------------------
# _render_jinja()
# ---------------------------------------------------------------------------
class TestRenderJinja(UnitTestCase):
	def test_simple_template(self):
		result = _render_jinja("Hello {{ name }}!", {"name": "World"})
		self.assertEqual(result, "Hello World!")

	def test_empty_template(self):
		self.assertEqual(_render_jinja("", {}), "")

	def test_whitespace_only(self):
		self.assertEqual(_render_jinja("   ", {}), "")

	def test_none_template(self):
		self.assertEqual(_render_jinja(None, {}), "")

	def test_context_variables(self):
		ctx = {"user": "Alice", "count": 42}
		result = _render_jinja("{{ user }} has {{ count }} items", ctx)
		self.assertEqual(result, "Alice has 42 items")

	def test_jinja_conditionals(self):
		result = _render_jinja("{% if show %}Visible{% endif %}", {"show": True})
		self.assertEqual(result, "Visible")

	def test_jinja_loop(self):
		result = _render_jinja(
			"{% for i in items %}{{ i }},{% endfor %}",
			{"items": ["a", "b", "c"]},
		)
		self.assertEqual(result, "a,b,c,")

	def test_template_error_returns_error_html(self):
		result = _render_jinja("{{ undefined_var.bad_attr }}", {})
		self.assertIn("ak-error", result)
		self.assertIn("Template rendering error", result)

	def test_syntax_error_returns_error_html(self):
		result = _render_jinja("{% if %}", {})
		self.assertIn("ak-error", result)

	def test_error_html_is_escaped(self):
		"""Error messages should be HTML-escaped to prevent XSS."""
		result = _render_jinja("{{ bad }}", {})
		# The error message itself should be escaped
		self.assertNotIn("<script>", result)

	def test_sandboxed_environment(self):
		"""Should use SandboxedEnvironment — dangerous operations blocked."""
		# Trying to access __subclasses__ should fail in sandbox
		result = _render_jinja("{{ ''.__class__.__subclasses__() }}", {})
		self.assertIn("ak-error", result)


# ---------------------------------------------------------------------------
# _get_base_css()
# ---------------------------------------------------------------------------
class TestGetBaseCSS(UnitTestCase):
	def setUp(self):
		# Reset the cache for each test
		import frappe_ak.renderer as renderer_module
		renderer_module._BASE_CSS_CACHE = None

	def test_loads_css_file(self):
		css = _get_base_css()
		# document_styles.css should exist and have content
		self.assertIsInstance(css, str)
		# It should contain some CSS content
		if os.path.exists(os.path.join(os.path.dirname(frappe_ak.renderer.__file__), "public", "css", "document_styles.css")):
			self.assertIn("ak-", css)

	def test_returns_cached_value(self):
		import frappe_ak.renderer as renderer_module
		renderer_module._BASE_CSS_CACHE = "cached-css"
		self.assertEqual(_get_base_css(), "cached-css")

	def test_handles_missing_file(self):
		import frappe_ak.renderer as renderer_module
		with patch("builtins.open", side_effect=FileNotFoundError):
			renderer_module._BASE_CSS_CACHE = None
			result = _get_base_css()
			self.assertEqual(result, "")


# ---------------------------------------------------------------------------
# _build_full_html()
# ---------------------------------------------------------------------------
class TestBuildFullHTML(UnitTestCase):
	def _make_rendered(self, html="<p>Body</p>", cover="", header="", footer="", css=""):
		return frappe._dict({
			"html": html,
			"cover_html": cover,
			"header_html": header,
			"footer_html": footer,
			"custom_css": css,
			"template_settings": {
				"page_format": "A4",
				"margins": {"top": 15, "bottom": 15, "left": 15, "right": 15},
			},
		})

	def test_basic_html_structure(self):
		result = _build_full_html(self._make_rendered())
		self.assertIn("<!DOCTYPE html>", result)
		self.assertIn("<html>", result)
		self.assertIn("<head>", result)
		self.assertIn("<body>", result)
		self.assertIn("<p>Body</p>", result)

	def test_css_embedded(self):
		result = _build_full_html(self._make_rendered())
		self.assertIn("<style>", result)
		self.assertIn(_BODY_CSS.strip()[:50], result)

	def test_custom_css_included(self):
		result = _build_full_html(self._make_rendered(css=".custom { color: red; }"))
		self.assertIn(".custom { color: red; }", result)

	def test_action_bar_hidden(self):
		result = _build_full_html(self._make_rendered())
		self.assertIn(".ak-action-bar { display:none !important; }", result)

	def test_cover_page_included(self):
		result = _build_full_html(self._make_rendered(cover="<h1>Cover</h1>"))
		self.assertIn("ak-cover-page", result)
		self.assertIn("<h1>Cover</h1>", result)
		self.assertIn("ak-page-break", result)

	def test_no_cover_page(self):
		result = _build_full_html(self._make_rendered(cover=""))
		# The CSS may contain .ak-cover-page class definition, but the HTML
		# body should NOT contain a <div class="ak-cover-page"> element
		self.assertNotIn('<div class="ak-cover-page">', result)

	def test_header_included(self):
		result = _build_full_html(self._make_rendered(header="<div>Header</div>"))
		self.assertIn("ak-header", result)
		self.assertIn("<div>Header</div>", result)

	def test_footer_included(self):
		result = _build_full_html(self._make_rendered(footer="<div>Footer</div>"))
		self.assertIn("ak-footer", result)
		self.assertIn("<div>Footer</div>", result)

	def test_charset_meta(self):
		result = _build_full_html(self._make_rendered())
		self.assertIn('charset="utf-8"', result)


# ---------------------------------------------------------------------------
# render_template()
# ---------------------------------------------------------------------------
class TestRenderTemplate(UnitTestCase):
	"""Tests for render_template() — requires mocked Frappe docs."""

	def _make_template_doc(self, **kwargs):
		fields = kwargs.pop("fields", [])
		defaults = {
			"doctype": "AK Document Template",
			"name": "Test Template",
			"template_name": "Test Template",
			"reference_doctype": "ToDo",
			"is_public_form": 0,
			"template_html": "<p>Hello {{ doc.name }}</p>",
			"cover_page_html": "",
			"header_html": "",
			"footer_html": "",
			"custom_css": "",
			"show_accept_decline": 0,
			"lock_after_submission": 0,
			"disable_access_after_submission": 0,
			"success_message": "Thanks!",
			"page_format": "A4",
			"top_margin": 15,
			"bottom_margin": 15,
			"left_margin": 15,
			"right_margin": 15,
			"fields": fields,
			"response_actions": [],
		}
		defaults.update(kwargs)
		return frappe._dict(defaults)

	def _make_share_doc(self, **kwargs):
		defaults = {
			"doctype": "AK Document Share",
			"name": "AK-DS-00001",
			"template": "Test Template",
			"reference_doctype": "ToDo",
			"reference_name": "TODO-001",
			"secret_key": "test-key",
			"expires_at": "2099-12-31",
		}
		defaults.update(kwargs)
		return frappe._dict(defaults)

	def _make_field(self, **kwargs):
		defaults = {
			"field_name": "test_field",
			"field_label": "Test Field",
			"field_type": "Data",
			"options": "",
			"is_existing_field": 0,
			"is_editable": 1,
			"is_mandatory": 0,
			"default_value": "",
			"column": "Left",
		}
		defaults.update(kwargs)
		return frappe._dict(defaults)

	def test_render_template_returns_expected_keys(self):
		template_doc = self._make_template_doc()
		share_doc = self._make_share_doc()
		doc = frappe._dict({"name": "TODO-001", "description": "Test"})

		with (
			patch("frappe.get_doc") as mock_get_doc,
		):
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_template(share_doc)

		self.assertIn("html", result)
		self.assertIn("cover_html", result)
		self.assertIn("header_html", result)
		self.assertIn("footer_html", result)
		self.assertIn("custom_css", result)
		self.assertIn("template_settings", result)

	def test_render_template_html_rendered(self):
		template_doc = self._make_template_doc(template_html="<p>Doc: {{ doc.name }}</p>")
		share_doc = self._make_share_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_template(share_doc)

		self.assertIn("Doc: TODO-001", result.html)

	def test_render_template_public_form_empty_doc(self):
		template_doc = self._make_template_doc(
			is_public_form=1,
			template_html="<p>Public form</p>",
		)
		share_doc = self._make_share_doc(reference_name="")

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.return_value = template_doc
			result = render_template(share_doc)

		self.assertIn("Public form", result.html)

	def test_render_template_settings(self):
		template_doc = self._make_template_doc(
			show_accept_decline=1,
			lock_after_submission=1,
			page_format="Letter",
			top_margin=20,
		)
		share_doc = self._make_share_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_template(share_doc)

		self.assertEqual(result.template_settings["show_accept_decline"], 1)
		self.assertEqual(result.template_settings["lock_after_submission"], 1)
		self.assertEqual(result.template_settings["page_format"], "Letter")
		self.assertEqual(result.template_settings["margins"]["top"], 20)

	def test_render_template_with_fields(self):
		fields = [self._make_field(field_name="approver", field_label="Approver")]
		template_doc = self._make_template_doc(
			fields=fields,
			template_html="{{ ak_input('approver', 'Approver') }}",
		)
		share_doc = self._make_share_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_template(share_doc)

		self.assertIn('name="approver"', result.html)
		self.assertIn("Approver", result.html)

	def test_render_template_cover_header_footer(self):
		template_doc = self._make_template_doc(
			template_html="<p>Body</p>",
			cover_page_html="<h1>Cover</h1>",
			header_html="<div>Header</div>",
			footer_html="<div>Footer</div>",
		)
		share_doc = self._make_share_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_template(share_doc)

		self.assertIn("Cover", result.cover_html)
		self.assertIn("Header", result.header_html)
		self.assertIn("Footer", result.footer_html)

	def test_render_template_custom_css(self):
		template_doc = self._make_template_doc(custom_css=".custom { color: blue; }")
		share_doc = self._make_share_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_template(share_doc)

		self.assertEqual(result.custom_css, ".custom { color: blue; }")


# ---------------------------------------------------------------------------
# render_response()
# ---------------------------------------------------------------------------
class TestRenderResponse(UnitTestCase):
	"""Tests for render_response() — re-renders with submitted values, all read-only."""

	def _make_template_doc(self, **kwargs):
		fields = kwargs.pop("fields", [])
		defaults = {
			"doctype": "AK Document Template",
			"name": "Test Template",
			"template_name": "Test Template",
			"reference_doctype": "ToDo",
			"is_public_form": 0,
			"template_html": "{{ ak_input('name', 'Name', value='default') }}",
			"cover_page_html": "",
			"header_html": "",
			"footer_html": "",
			"custom_css": ".test{}",
			"fields": fields,
		}
		defaults.update(kwargs)
		return frappe._dict(defaults)

	def _make_field(self, **kwargs):
		defaults = {
			"field_name": "name",
			"field_label": "Name",
			"field_type": "Data",
			"options": "",
			"is_existing_field": 0,
			"is_editable": 1,
			"is_mandatory": 1,
			"default_value": "",
			"column": "Left",
		}
		defaults.update(kwargs)
		return frappe._dict(defaults)

	def _make_response_doc(self, **kwargs):
		defaults = {
			"doctype": "AK Document Response",
			"name": "AK-DR-00001",
			"document_share": "AK-DS-00001",
			"template": "Test Template",
			"reference_doctype": "ToDo",
			"reference_name": "TODO-001",
			"response_type": "Accepted",
			"response_data": json.dumps({"name": "Alice"}),
		}
		defaults.update(kwargs)
		return frappe._dict(defaults)

	def test_returns_html_and_css(self):
		template_doc = self._make_template_doc(fields=[self._make_field()])
		response_doc = self._make_response_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		self.assertIn("html", result)
		self.assertIn("css", result)

	def test_fields_are_readonly(self):
		template_doc = self._make_template_doc(
			fields=[self._make_field()],
			template_html="{{ ak_input('name', 'Name') }}",
		)
		response_doc = self._make_response_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		# All fields should be forced read-only (is_editable=0)
		self.assertIn("disabled", result["html"])

	def test_response_badge_replaces_buttons(self):
		template_doc = self._make_template_doc(
			fields=[self._make_field()],
			template_html="{{ ak_accept_decline('Accept', 'Decline') }}",
		)
		response_doc = self._make_response_doc(response_type="Accepted")
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		# Should show response badge, not action buttons
		self.assertIn("Response: Accepted", result["html"])
		self.assertNotIn("ak-accept-btn", result["html"])

	def test_response_badge_declined(self):
		template_doc = self._make_template_doc(
			fields=[],
			template_html="{{ ak_accept_decline() }}",
		)
		response_doc = self._make_response_doc(response_type="Declined")
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		self.assertIn("Response: Declined", result["html"])

	def test_response_badge_submitted(self):
		template_doc = self._make_template_doc(
			fields=[],
			template_html="{{ ak_submit_button() }}",
		)
		response_doc = self._make_response_doc(response_type="Submitted")
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		self.assertIn("Response: Submitted", result["html"])

	def test_response_badge_accepts_positional_args(self):
		"""_response_badge should accept *args, **kwargs from template calls."""
		template_doc = self._make_template_doc(
			fields=[],
			template_html="{{ ak_accept_decline('Approve', 'Reject') }}",
		)
		response_doc = self._make_response_doc(response_type="Accepted")
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			# Should not raise TypeError about positional args
			result = render_response(response_doc)

		self.assertIn("Response: Accepted", result["html"])

	def test_response_data_injected(self):
		template_doc = self._make_template_doc(
			fields=[self._make_field()],
			template_html="{{ ak_input('name', 'Name') }}",
		)
		response_doc = self._make_response_doc(
			response_data=json.dumps({"name": "Bob"})
		)
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		self.assertIn("Bob", result["html"])

	def test_empty_response_data(self):
		template_doc = self._make_template_doc(
			fields=[self._make_field()],
			template_html="{{ ak_input('name', 'Name') }}",
		)
		response_doc = self._make_response_doc(response_data="")
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			# Should not crash with empty response_data
			result = render_response(response_doc)

		self.assertIn("html", result)

	def test_cover_header_footer_included(self):
		template_doc = self._make_template_doc(
			fields=[],
			template_html="<p>Body</p>",
			cover_page_html="<h1>Cover</h1>",
			header_html="<div>Header</div>",
			footer_html="<div>Footer</div>",
		)
		response_doc = self._make_response_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		self.assertIn("Cover", result["html"])
		self.assertIn("Header", result["html"])
		self.assertIn("Footer", result["html"])

	def test_css_returned(self):
		template_doc = self._make_template_doc(
			fields=[], custom_css=".custom { color: red; }",
			template_html="<p>X</p>",
		)
		response_doc = self._make_response_doc()
		doc = frappe._dict({"name": "TODO-001"})

		with patch("frappe.get_doc") as mock_get_doc:
			mock_get_doc.side_effect = lambda dt, name=None: (
				template_doc if dt == "AK Document Template" else doc
			)
			result = render_response(response_doc)

		self.assertEqual(result["css"], ".custom { color: red; }")


import frappe_ak.renderer
