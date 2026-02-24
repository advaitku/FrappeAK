"""Tests for template_helpers.py — all Jinja2 helper functions for Doc Designer."""

import frappe
from frappe.tests import UnitTestCase
from markupsafe import Markup

from frappe_ak.template_helpers import (
	_attr,
	_field_wrapper,
	ak_input,
	ak_textarea,
	ak_date,
	ak_datetime,
	ak_checkbox,
	ak_select,
	ak_field_table,
	ak_items_table,
	ak_accept_decline,
	ak_submit_button,
	_render_table_field,
)


# ---------------------------------------------------------------------------
# _attr()
# ---------------------------------------------------------------------------
class TestAttr(UnitTestCase):
	def test_truthy_string(self):
		self.assertEqual(_attr("placeholder", "Enter name"), ' placeholder="Enter name"')

	def test_boolean_true(self):
		self.assertEqual(_attr("required", True), " required")

	def test_falsy_value_returns_empty(self):
		self.assertEqual(_attr("placeholder", ""), "")
		self.assertEqual(_attr("placeholder", None), "")

	def test_html_escaping(self):
		result = _attr("value", '<script>alert("xss")</script>')
		self.assertNotIn("<script>", result)
		self.assertIn("&lt;script&gt;", result)

	def test_numeric_value(self):
		result = _attr("rows", 5)
		self.assertEqual(result, ' rows="5"')


# ---------------------------------------------------------------------------
# _field_wrapper()
# ---------------------------------------------------------------------------
class TestFieldWrapper(UnitTestCase):
	def test_editable_field(self):
		html = str(_field_wrapper("name", "Data", True, False, "<input/>"))
		self.assertIn('class="ak-field"', html)
		self.assertIn('data-editable="1"', html)
		self.assertNotIn("ak-field-readonly", html)

	def test_readonly_field(self):
		html = str(_field_wrapper("name", "Data", False, False, "<input/>"))
		self.assertIn("ak-field-readonly", html)
		self.assertNotIn('data-editable="1"', html)

	def test_mandatory_field(self):
		html = str(_field_wrapper("name", "Data", True, True, "<input/>"))
		self.assertIn("ak-field-mandatory", html)
		self.assertIn('data-mandatory="1"', html)

	def test_data_attributes(self):
		html = str(_field_wrapper("email", "Data", True, False, "<input/>"))
		self.assertIn('data-fieldname="email"', html)
		self.assertIn('data-fieldtype="Data"', html)

	def test_returns_markup(self):
		result = _field_wrapper("f", "Data", True, False, "x")
		self.assertIsInstance(result, Markup)

	def test_content_included(self):
		html = str(_field_wrapper("f", "Data", True, False, '<input type="text"/>'))
		self.assertIn('<input type="text"/>', html)


# ---------------------------------------------------------------------------
# ak_input()
# ---------------------------------------------------------------------------
class TestAkInput(UnitTestCase):
	def test_basic_text_input(self):
		html = str(ak_input("full_name", label="Full Name"))
		self.assertIn('name="full_name"', html)
		self.assertIn('type="text"', html)
		self.assertIn("Full Name", html)
		self.assertIn("ak-field-label", html)

	def test_value_pre_filled(self):
		html = str(ak_input("email", value="test@example.com"))
		self.assertIn('value="test@example.com"', html)

	def test_placeholder(self):
		html = str(ak_input("name", placeholder="Enter your name"))
		self.assertIn('placeholder="Enter your name"', html)

	def test_mandatory_adds_required(self):
		html = str(ak_input("name", mandatory=True))
		self.assertIn(" required", html)
		self.assertIn("ak-field-mandatory", html)

	def test_readonly_adds_disabled(self):
		html = str(ak_input("name", editable=False))
		self.assertIn(" disabled", html)
		self.assertIn("ak-field-readonly", html)

	def test_number_input_type(self):
		html = str(ak_input("qty", input_type="number"))
		self.assertIn('type="number"', html)

	def test_email_input_type(self):
		html = str(ak_input("email", input_type="email"))
		self.assertIn('type="email"', html)

	def test_xss_value_escaped(self):
		html = str(ak_input("name", value='<script>alert("xss")</script>'))
		self.assertNotIn("<script>", html)
		self.assertIn("&lt;script&gt;", html)

	def test_xss_label_escaped(self):
		html = str(ak_input("name", label='<b>Bold</b>'))
		self.assertNotIn("<b>Bold</b>", html)

	def test_no_label(self):
		html = str(ak_input("name"))
		self.assertNotIn("ak-field-label", html)

	def test_returns_markup(self):
		result = ak_input("name")
		self.assertIsInstance(result, Markup)

	def test_empty_value(self):
		html = str(ak_input("name", value=""))
		self.assertIn('value=""', html)

	def test_none_value_treated_as_empty(self):
		html = str(ak_input("name", value=None))
		self.assertIn('value=""', html)


# ---------------------------------------------------------------------------
# ak_textarea()
# ---------------------------------------------------------------------------
class TestAkTextarea(UnitTestCase):
	def test_basic_textarea(self):
		html = str(ak_textarea("notes", label="Notes"))
		self.assertIn("<textarea", html)
		self.assertIn('name="notes"', html)
		self.assertIn("Notes", html)

	def test_rows(self):
		html = str(ak_textarea("notes", rows=6))
		self.assertIn('rows="6"', html)

	def test_default_rows(self):
		html = str(ak_textarea("notes"))
		self.assertIn('rows="4"', html)

	def test_value_inside_textarea(self):
		html = str(ak_textarea("notes", value="Hello world"))
		self.assertIn(">Hello world</textarea>", html)

	def test_placeholder(self):
		html = str(ak_textarea("notes", placeholder="Type here"))
		self.assertIn('placeholder="Type here"', html)

	def test_mandatory(self):
		html = str(ak_textarea("notes", mandatory=True))
		self.assertIn(" required", html)

	def test_readonly(self):
		html = str(ak_textarea("notes", editable=False))
		self.assertIn(" disabled", html)

	def test_xss_value_escaped(self):
		html = str(ak_textarea("notes", value="<script>bad</script>"))
		self.assertNotIn("<script>bad</script>", html)

	def test_field_wrapper_type(self):
		html = str(ak_textarea("notes"))
		self.assertIn('data-fieldtype="Text"', html)


# ---------------------------------------------------------------------------
# ak_date()
# ---------------------------------------------------------------------------
class TestAkDate(UnitTestCase):
	def test_basic_date(self):
		html = str(ak_date("delivery_date", label="Delivery Date"))
		self.assertIn('type="date"', html)
		self.assertIn('name="delivery_date"', html)
		self.assertIn("Delivery Date", html)

	def test_value(self):
		html = str(ak_date("dob", value="2024-01-15"))
		self.assertIn('value="2024-01-15"', html)

	def test_mandatory(self):
		html = str(ak_date("dob", mandatory=True))
		self.assertIn(" required", html)

	def test_readonly(self):
		html = str(ak_date("dob", editable=False))
		self.assertIn(" disabled", html)

	def test_field_type(self):
		html = str(ak_date("dob"))
		self.assertIn('data-fieldtype="Date"', html)


# ---------------------------------------------------------------------------
# ak_datetime()
# ---------------------------------------------------------------------------
class TestAkDatetime(UnitTestCase):
	def test_basic_datetime(self):
		html = str(ak_datetime("event_time", label="Event Time"))
		self.assertIn('type="datetime-local"', html)
		self.assertIn('name="event_time"', html)

	def test_value_conversion(self):
		"""Frappe datetime (space-separated) should be converted to T-separated."""
		html = str(ak_datetime("ts", value="2024-06-15 14:30:00"))
		self.assertIn('value="2024-06-15T14:30"', html)

	def test_value_truncation_to_16_chars(self):
		html = str(ak_datetime("ts", value="2024-06-15 14:30:45.123456"))
		# After space→T conversion: "2024-06-15T14:30" (16 chars)
		self.assertIn('value="2024-06-15T14:30"', html)

	def test_empty_value(self):
		html = str(ak_datetime("ts", value=""))
		self.assertIn('value=""', html)

	def test_mandatory(self):
		html = str(ak_datetime("ts", mandatory=True))
		self.assertIn(" required", html)

	def test_readonly(self):
		html = str(ak_datetime("ts", editable=False))
		self.assertIn(" disabled", html)

	def test_field_type(self):
		html = str(ak_datetime("ts"))
		self.assertIn('data-fieldtype="Datetime"', html)


# ---------------------------------------------------------------------------
# ak_checkbox()
# ---------------------------------------------------------------------------
class TestAkCheckbox(UnitTestCase):
	def test_unchecked(self):
		html = str(ak_checkbox("agree", label="I agree"))
		self.assertIn('type="checkbox"', html)
		self.assertIn('name="agree"', html)
		self.assertIn("I agree", html)
		self.assertNotIn(" checked", html)

	def test_checked(self):
		html = str(ak_checkbox("agree", checked=True))
		self.assertIn(" checked", html)

	def test_disabled(self):
		html = str(ak_checkbox("agree", editable=False))
		self.assertIn(" disabled", html)

	def test_label_inline(self):
		html = str(ak_checkbox("agree", label="Terms"))
		self.assertIn("ak-checkbox-label", html)
		self.assertIn("Terms", html)

	def test_field_type(self):
		html = str(ak_checkbox("agree"))
		self.assertIn('data-fieldtype="Check"', html)

	def test_never_mandatory_class(self):
		"""Checkboxes never get the mandatory wrapper class."""
		html = str(ak_checkbox("agree"))
		self.assertNotIn("ak-field-mandatory", html)


# ---------------------------------------------------------------------------
# ak_select()
# ---------------------------------------------------------------------------
class TestAkSelect(UnitTestCase):
	def test_basic_select(self):
		html = str(ak_select("status", label="Status", options=["Open", "Closed"]))
		self.assertIn("<select", html)
		self.assertIn('name="status"', html)
		self.assertIn("Status", html)

	def test_options_as_list(self):
		html = str(ak_select("color", options=["Red", "Blue", "Green"]))
		self.assertIn(">Red</option>", html)
		self.assertIn(">Blue</option>", html)
		self.assertIn(">Green</option>", html)

	def test_options_as_newline_string(self):
		html = str(ak_select("color", options="Red\nBlue\nGreen"))
		self.assertIn(">Red</option>", html)
		self.assertIn(">Blue</option>", html)

	def test_default_placeholder(self):
		html = str(ak_select("color", options=["Red"]))
		self.assertIn("-- Select --", html)

	def test_selected_value(self):
		html = str(ak_select("color", options=["Red", "Blue"], value="Blue"))
		# Blue should be selected
		self.assertIn('value="Blue" selected', html)
		# Red should NOT be selected
		self.assertNotIn('value="Red" selected', html)

	def test_empty_options(self):
		html = str(ak_select("color"))
		self.assertIn("-- Select --", html)
		# Should only have the placeholder option
		self.assertEqual(html.count("<option"), 1)

	def test_mandatory(self):
		html = str(ak_select("color", options=["Red"], mandatory=True))
		self.assertIn(" required", html)

	def test_readonly(self):
		html = str(ak_select("color", options=["Red"], editable=False))
		self.assertIn(" disabled", html)

	def test_xss_option_escaped(self):
		html = str(ak_select("x", options=['<script>bad</script>']))
		self.assertNotIn("<script>", html)

	def test_field_type(self):
		html = str(ak_select("x"))
		self.assertIn('data-fieldtype="Select"', html)

	def test_options_with_empty_lines(self):
		html = str(ak_select("x", options="Red\n\nBlue\n"))
		self.assertIn(">Red</option>", html)
		self.assertIn(">Blue</option>", html)
		# Empty lines should be stripped
		self.assertNotIn('value="">', html.split("-- Select --")[1])


# ---------------------------------------------------------------------------
# ak_field_table()
# ---------------------------------------------------------------------------
class TestAkFieldTable(UnitTestCase):
	def _make_field(self, name="f1", label="Field 1", ftype="Data",
	                editable=1, mandatory=0, default="", column="Left", options=""):
		return {
			"field_name": name,
			"field_label": label,
			"field_type": ftype,
			"is_existing_field": 0,
			"is_editable": editable,
			"is_mandatory": mandatory,
			"default_value": default,
			"column": column,
			"options": options,
		}

	def test_empty_fields(self):
		result = str(ak_field_table([]))
		self.assertEqual(result, "")

	def test_single_column_layout(self):
		fields = [self._make_field("name", "Name"), self._make_field("email", "Email")]
		html = str(ak_field_table(fields, columns=1))
		self.assertIn("ak-field-table", html)
		self.assertIn('name="name"', html)
		self.assertIn('name="email"', html)
		self.assertNotIn("ak-two-col", html)

	def test_two_column_layout(self):
		fields = [
			self._make_field("name", "Name", column="Left"),
			self._make_field("email", "Email", column="Right"),
		]
		html = str(ak_field_table(fields, columns=2))
		self.assertIn("ak-two-col", html)
		self.assertIn("ak-col-left", html)
		self.assertIn("ak-col-right", html)

	def test_field_type_routing_data(self):
		fields = [self._make_field("name", "Name", "Data")]
		html = str(ak_field_table(fields))
		self.assertIn('type="text"', html)

	def test_field_type_routing_int(self):
		fields = [self._make_field("qty", "Qty", "Int")]
		html = str(ak_field_table(fields))
		self.assertIn('type="number"', html)

	def test_field_type_routing_text(self):
		fields = [self._make_field("notes", "Notes", "Text")]
		html = str(ak_field_table(fields))
		self.assertIn("<textarea", html)

	def test_field_type_routing_date(self):
		fields = [self._make_field("dob", "DOB", "Date")]
		html = str(ak_field_table(fields))
		self.assertIn('type="date"', html)

	def test_field_type_routing_check(self):
		fields = [self._make_field("agree", "Agree", "Check")]
		html = str(ak_field_table(fields))
		self.assertIn('type="checkbox"', html)

	def test_field_type_routing_select(self):
		fields = [self._make_field("status", "Status", "Select", options="Open\nClosed")]
		html = str(ak_field_table(fields))
		self.assertIn("<select", html)
		self.assertIn(">Open</option>", html)

	def test_default_value_applied(self):
		fields = [self._make_field("city", "City", default="London")]
		html = str(ak_field_table(fields))
		self.assertIn('value="London"', html)

	def test_existing_field_pre_fill(self):
		"""Existing fields should take value from doc, not default."""
		field = self._make_field("description", "Description", default="fallback")
		field["is_existing_field"] = 1
		doc = frappe._dict({"description": "From document"})
		html = str(ak_field_table([field], doc=doc))
		self.assertIn('value="From document"', html)

	def test_existing_field_fallback_to_default(self):
		"""If doc value is None, fall back to default."""
		field = self._make_field("notes", "Notes", default="default notes")
		field["is_existing_field"] = 1
		doc = frappe._dict({"notes": None})
		html = str(ak_field_table([field], doc=doc))
		self.assertIn('value="default notes"', html)


# ---------------------------------------------------------------------------
# _render_table_field()
# ---------------------------------------------------------------------------
class TestRenderTableField(UnitTestCase):
	def test_data_type(self):
		field = {"field_name": "f", "field_label": "F", "field_type": "Data",
		         "is_editable": True, "is_mandatory": False, "default_value": "", "options": ""}
		html = _render_table_field(field)
		self.assertIn('type="text"', html)

	def test_int_type(self):
		field = {"field_name": "f", "field_label": "F", "field_type": "Int",
		         "is_editable": True, "is_mandatory": False, "default_value": "", "options": ""}
		html = _render_table_field(field)
		self.assertIn('type="number"', html)

	def test_currency_type(self):
		field = {"field_name": "f", "field_label": "F", "field_type": "Currency",
		         "is_editable": True, "is_mandatory": False, "default_value": "", "options": ""}
		html = _render_table_field(field)
		self.assertIn('type="number"', html)

	def test_text_type(self):
		field = {"field_name": "f", "field_label": "F", "field_type": "Text",
		         "is_editable": True, "is_mandatory": False, "default_value": "", "options": ""}
		html = _render_table_field(field)
		self.assertIn("<textarea", html)

	def test_datetime_type(self):
		field = {"field_name": "f", "field_label": "F", "field_type": "Datetime",
		         "is_editable": True, "is_mandatory": False, "default_value": "", "options": ""}
		html = _render_table_field(field)
		self.assertIn('type="datetime-local"', html)

	def test_unknown_type_defaults_to_input(self):
		field = {"field_name": "f", "field_label": "F", "field_type": "SomeUnknownType",
		         "is_editable": True, "is_mandatory": False, "default_value": "", "options": ""}
		html = _render_table_field(field)
		self.assertIn('type="text"', html)

	def test_doc_value_overrides_default(self):
		field = {"field_name": "status", "field_label": "Status", "field_type": "Data",
		         "is_editable": True, "is_mandatory": False, "default_value": "default",
		         "options": "", "is_existing_field": 1}
		doc = frappe._dict({"status": "FromDoc"})
		html = _render_table_field(field, doc=doc)
		self.assertIn('value="FromDoc"', html)


# ---------------------------------------------------------------------------
# ak_items_table()
# ---------------------------------------------------------------------------
class TestAkItemsTable(UnitTestCase):
	def _make_doc(self, items=None, grand_total=0):
		return frappe._dict({
			"items": items or [],
			"grand_total": grand_total,
		})

	def test_empty_items(self):
		doc = self._make_doc()
		html = str(ak_items_table(doc))
		self.assertIn("ak-items-table", html)
		self.assertIn("<thead>", html)
		# No data rows
		self.assertNotIn('<td class="ak-items-col-num">1</td>', html)

	def test_items_rendered(self):
		items = [
			frappe._dict({"item_name": "Widget", "qty": 10, "rate": 100, "amount": 1000}),
			frappe._dict({"item_name": "Gadget", "qty": 5, "rate": 50, "amount": 250}),
		]
		doc = self._make_doc(items, grand_total=1250)
		html = str(ak_items_table(doc))
		self.assertIn("Widget", html)
		self.assertIn("Gadget", html)

	def test_row_numbering(self):
		items = [frappe._dict({"item_name": "A", "qty": 1, "rate": 10, "amount": 10})]
		doc = self._make_doc(items)
		html = str(ak_items_table(doc))
		self.assertIn(">1</td>", html)

	def test_currency_formatting(self):
		items = [frappe._dict({"item_name": "X", "qty": 1, "rate": 1234.56, "amount": 1234.56})]
		doc = self._make_doc(items)
		html = str(ak_items_table(doc))
		self.assertIn("$1,234.56", html)

	def test_qty_formatting(self):
		items = [frappe._dict({"item_name": "X", "qty": 10.0, "rate": 5, "amount": 50})]
		doc = self._make_doc(items)
		html = str(ak_items_table(doc))
		self.assertIn("10", html)

	def test_total_row(self):
		doc = self._make_doc(grand_total=5000)
		html = str(ak_items_table(doc, show_total=True))
		self.assertIn("Total", html)
		self.assertIn("$5,000.00", html)

	def test_no_total_row(self):
		doc = self._make_doc(grand_total=5000)
		html = str(ak_items_table(doc, show_total=False))
		self.assertNotIn("<tfoot>", html)

	def test_custom_columns(self):
		items = [frappe._dict({"item_name": "X", "description": "Desc"})]
		doc = self._make_doc(items)
		html = str(ak_items_table(doc, columns=["item_name", "description"]))
		self.assertIn("Item Name", html)
		self.assertIn("Description", html)
		self.assertNotIn("Qty", html)

	def test_default_columns(self):
		html = str(ak_items_table(self._make_doc()))
		self.assertIn("Item Name", html)
		self.assertIn("Qty", html)
		self.assertIn("Rate", html)
		self.assertIn("Amount", html)

	def test_custom_currency_symbol(self):
		doc = self._make_doc(grand_total=100)
		html = str(ak_items_table(doc, currency_symbol="£"))
		self.assertIn("£100.00", html)

	def test_doc_without_items_attribute(self):
		doc = frappe._dict({})
		html = str(ak_items_table(doc))
		# Should not crash, just render empty table
		self.assertIn("ak-items-table", html)


# ---------------------------------------------------------------------------
# ak_accept_decline()
# ---------------------------------------------------------------------------
class TestAkAcceptDecline(UnitTestCase):
	def test_default_labels(self):
		html = str(ak_accept_decline())
		self.assertIn("Accept", html)
		self.assertIn("Decline", html)

	def test_custom_labels(self):
		html = str(ak_accept_decline("Approve", "Reject"))
		self.assertIn("Approve", html)
		self.assertIn("Reject", html)

	def test_action_bar_class(self):
		html = str(ak_accept_decline())
		self.assertIn("ak-action-bar", html)

	def test_data_action_attributes(self):
		html = str(ak_accept_decline())
		self.assertIn('data-action="Accepted"', html)
		self.assertIn('data-action="Declined"', html)

	def test_button_classes(self):
		html = str(ak_accept_decline())
		self.assertIn("ak-accept-btn", html)
		self.assertIn("ak-decline-btn", html)

	def test_pdf_button_present(self):
		html = str(ak_accept_decline())
		self.assertIn("ak-download-pdf", html)
		self.assertIn("Print / Save PDF", html)

	def test_returns_markup(self):
		result = ak_accept_decline()
		self.assertIsInstance(result, Markup)

	def test_xss_label_escaped(self):
		html = str(ak_accept_decline('<script>xss</script>', 'OK'))
		self.assertNotIn("<script>", html)


# ---------------------------------------------------------------------------
# ak_submit_button()
# ---------------------------------------------------------------------------
class TestAkSubmitButton(UnitTestCase):
	def test_default_label(self):
		html = str(ak_submit_button())
		self.assertIn("Submit", html)

	def test_custom_label(self):
		html = str(ak_submit_button("Send Response"))
		self.assertIn("Send Response", html)

	def test_action_bar_class(self):
		html = str(ak_submit_button())
		self.assertIn("ak-action-bar", html)

	def test_data_action(self):
		html = str(ak_submit_button())
		self.assertIn('data-action="Submitted"', html)

	def test_submit_button_class(self):
		html = str(ak_submit_button())
		self.assertIn("ak-submit-btn", html)

	def test_pdf_button_present(self):
		html = str(ak_submit_button())
		self.assertIn("ak-download-pdf", html)
		self.assertIn("Print / Save PDF", html)

	def test_returns_markup(self):
		result = ak_submit_button()
		self.assertIsInstance(result, Markup)

	def test_xss_label_escaped(self):
		html = str(ak_submit_button('<img onerror=alert(1)>'))
		self.assertNotIn("<img", html)
