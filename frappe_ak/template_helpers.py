"""Jinja2 helper functions for AK Document Templates.

These functions are registered in hooks.py via jenv and are available
in template HTML for generating interactive form fields.

Usage in templates:
    {{ ak_input("field_name", label="Label", editable=True, mandatory=True) }}
    {{ ak_textarea("notes", label="Notes") }}
    {{ ak_date("delivery_date", label="Delivery Date", value=doc.delivery_date) }}
    {{ ak_items_table(doc, columns=["item_name", "qty", "rate", "amount"]) }}
"""

import frappe
from markupsafe import Markup


def _attr(key, value):
    """Return an HTML attribute string if value is truthy."""
    if value is True:
        return f' {key}'
    if value:
        return f' {key}="{frappe.utils.escape_html(str(value))}"'
    return ""


def _field_wrapper(fieldname, field_type, editable, mandatory, content):
    """Wrap a field in the standard ak-field div."""
    classes = ["ak-field"]
    if not editable:
        classes.append("ak-field-readonly")
    if mandatory:
        classes.append("ak-field-mandatory")

    attrs = f'data-fieldname="{fieldname}" data-fieldtype="{field_type}"'
    if editable:
        attrs += ' data-editable="1"'
    if mandatory:
        attrs += ' data-mandatory="1"'

    return Markup(
        f'<div class="{" ".join(classes)}" {attrs}>'
        f'{content}'
        f'</div>'
    )


def ak_input(fieldname, label="", value="", placeholder="",
             editable=True, mandatory=False, input_type="text"):
    """Render an interactive text input field.

    Args:
        fieldname: Field name (used for form submission)
        label: Display label
        value: Pre-filled value
        placeholder: Placeholder text
        editable: Whether the recipient can edit this field
        mandatory: Whether this field is required
        input_type: HTML input type (text, number, email, tel, url)
    """
    escaped_val = frappe.utils.escape_html(str(value)) if value else ""
    label_html = f'<label class="ak-field-label">{frappe.utils.escape_html(label)}</label>' if label else ""
    req = ' required' if mandatory else ''
    disabled = ' disabled' if not editable else ''
    ph = f' placeholder="{frappe.utils.escape_html(placeholder)}"' if placeholder else ''

    input_html = (
        f'{label_html}'
        f'<input type="{input_type}" name="{fieldname}" '
        f'value="{escaped_val}"{ph}{req}{disabled} '
        f'class="ak-field-input" />'
    )

    return _field_wrapper(fieldname, "Data", editable, mandatory, input_html)


def ak_textarea(fieldname, label="", value="", rows=4,
                editable=True, mandatory=False, placeholder=""):
    """Render an interactive textarea field.

    Args:
        fieldname: Field name
        label: Display label
        value: Pre-filled value
        rows: Number of visible rows
        editable: Whether the recipient can edit
        mandatory: Whether required
        placeholder: Placeholder text
    """
    escaped_val = frappe.utils.escape_html(str(value)) if value else ""
    label_html = f'<label class="ak-field-label">{frappe.utils.escape_html(label)}</label>' if label else ""
    req = ' required' if mandatory else ''
    disabled = ' disabled' if not editable else ''
    ph = f' placeholder="{frappe.utils.escape_html(placeholder)}"' if placeholder else ''

    textarea_html = (
        f'{label_html}'
        f'<textarea name="{fieldname}" rows="{rows}"{req}{disabled}{ph} '
        f'class="ak-field-input">{escaped_val}</textarea>'
    )

    return _field_wrapper(fieldname, "Text", editable, mandatory, textarea_html)


def ak_date(fieldname, label="", value="", editable=True, mandatory=False):
    """Render a date picker field.

    Args:
        fieldname: Field name
        label: Display label
        value: Pre-filled date value (YYYY-MM-DD)
        editable: Whether the recipient can edit
        mandatory: Whether required
    """
    escaped_val = frappe.utils.escape_html(str(value)) if value else ""
    label_html = f'<label class="ak-field-label">{frappe.utils.escape_html(label)}</label>' if label else ""
    req = ' required' if mandatory else ''
    disabled = ' disabled' if not editable else ''

    date_html = (
        f'{label_html}'
        f'<input type="date" name="{fieldname}" value="{escaped_val}"{req}{disabled} '
        f'class="ak-field-input" />'
    )

    return _field_wrapper(fieldname, "Date", editable, mandatory, date_html)


def ak_datetime(fieldname, label="", value="", editable=True, mandatory=False):
    """Render a datetime picker field.

    Args:
        fieldname: Field name
        label: Display label
        value: Pre-filled datetime value
        editable: Whether the recipient can edit
        mandatory: Whether required
    """
    escaped_val = ""
    if value:
        # Convert Frappe datetime to HTML datetime-local format
        dt_str = str(value).replace(" ", "T")[:16]
        escaped_val = frappe.utils.escape_html(dt_str)

    label_html = f'<label class="ak-field-label">{frappe.utils.escape_html(label)}</label>' if label else ""
    req = ' required' if mandatory else ''
    disabled = ' disabled' if not editable else ''

    dt_html = (
        f'{label_html}'
        f'<input type="datetime-local" name="{fieldname}" value="{escaped_val}"{req}{disabled} '
        f'class="ak-field-input" />'
    )

    return _field_wrapper(fieldname, "Datetime", editable, mandatory, dt_html)


def ak_checkbox(fieldname, label="", checked=False, editable=True):
    """Render a checkbox field.

    Args:
        fieldname: Field name
        label: Display label
        checked: Whether pre-checked
        editable: Whether the recipient can toggle
    """
    chk = ' checked' if checked else ''
    disabled = ' disabled' if not editable else ''

    cb_html = (
        f'<label class="ak-field-label ak-checkbox-label">'
        f'<input type="checkbox" name="{fieldname}" value="1"{chk}{disabled} '
        f'class="ak-field-input" />'
        f' {frappe.utils.escape_html(label)}'
        f'</label>'
    )

    return _field_wrapper(fieldname, "Check", editable, False, cb_html)


def ak_select(fieldname, label="", options=None, value="",
              editable=True, mandatory=False):
    """Render a dropdown select field.

    Args:
        fieldname: Field name
        label: Display label
        options: List of option strings, or newline-separated string
        value: Pre-selected value
        editable: Whether the recipient can change
        mandatory: Whether required
    """
    if options is None:
        options = []
    if isinstance(options, str):
        options = [o.strip() for o in options.split("\n") if o.strip()]

    label_html = f'<label class="ak-field-label">{frappe.utils.escape_html(label)}</label>' if label else ""
    req = ' required' if mandatory else ''
    disabled = ' disabled' if not editable else ''

    opts_html = '<option value="">-- Select --</option>'
    for opt in options:
        selected = ' selected' if str(opt) == str(value) else ''
        opts_html += f'<option value="{frappe.utils.escape_html(str(opt))}"{selected}>{frappe.utils.escape_html(str(opt))}</option>'

    select_html = (
        f'{label_html}'
        f'<select name="{fieldname}"{req}{disabled} class="ak-field-input">'
        f'{opts_html}'
        f'</select>'
    )

    return _field_wrapper(fieldname, "Select", editable, mandatory, select_html)


def ak_field_table(fields, columns=1, doc=None):
    """Auto-generate a form table from a list of field definitions.

    This reads the AK Template Field child table entries and renders them
    as a structured form table.

    Args:
        fields: List of dicts with keys: field_name, field_label, field_type,
                options, is_editable, is_mandatory, default_value, column
                (typically passed from the template's fields child table)
        columns: 1 or 2 column layout
        doc: The Frappe document (for pre-filling existing field values)
    """
    if not fields:
        return Markup("")

    rows_html = ""

    if columns == 2:
        left_fields = [f for f in fields if f.get("column") in ("Left", None, "")]
        right_fields = [f for f in fields if f.get("column") == "Right"]
        max_rows = max(len(left_fields), len(right_fields))

        for i in range(max_rows):
            left_cell = _render_table_field(left_fields[i], doc) if i < len(left_fields) else ""
            right_cell = _render_table_field(right_fields[i], doc) if i < len(right_fields) else ""
            rows_html += f'<tr><td class="ak-col-left">{left_cell}</td><td class="ak-col-right">{right_cell}</td></tr>'
    else:
        for f in fields:
            cell = _render_table_field(f, doc)
            rows_html += f'<tr><td>{cell}</td></tr>'

    col_class = "ak-two-col" if columns == 2 else ""

    return Markup(
        f'<table class="ak-field-table {col_class}">'
        f'<tbody>{rows_html}</tbody>'
        f'</table>'
    )


def _render_table_field(field, doc=None):
    """Render a single field inside a form table cell."""
    fname = field.get("field_name", "")
    flabel = field.get("field_label", fname)
    ftype = field.get("field_type", "Data")
    editable = field.get("is_editable", True)
    mandatory = field.get("is_mandatory", False)
    default = field.get("default_value", "")
    options = field.get("options", "")

    # Pre-fill from document if available and field is an existing field
    value = default
    if doc and field.get("is_existing_field"):
        doc_val = doc.get(fname) if hasattr(doc, "get") else None
        if doc_val is not None:
            value = doc_val

    ftype_lower = ftype.lower()
    if ftype_lower in ("data", "small text", "int", "float", "currency"):
        input_type = "number" if ftype_lower in ("int", "float", "currency") else "text"
        return str(ak_input(fname, label=flabel, value=value,
                            editable=editable, mandatory=mandatory, input_type=input_type))
    elif ftype_lower == "text":
        return str(ak_textarea(fname, label=flabel, value=value,
                               editable=editable, mandatory=mandatory))
    elif ftype_lower == "date":
        return str(ak_date(fname, label=flabel, value=value,
                           editable=editable, mandatory=mandatory))
    elif ftype_lower == "datetime":
        return str(ak_datetime(fname, label=flabel, value=value,
                               editable=editable, mandatory=mandatory))
    elif ftype_lower == "check":
        return str(ak_checkbox(fname, label=flabel, checked=bool(value),
                               editable=editable))
    elif ftype_lower == "select":
        return str(ak_select(fname, label=flabel, options=options, value=value,
                             editable=editable, mandatory=mandatory))
    else:
        return str(ak_input(fname, label=flabel, value=value,
                            editable=editable, mandatory=mandatory))


def ak_items_table(doc, columns=None, show_total=True, total_field="grand_total",
                   currency_symbol="$"):
    """Render a pricing/items table from a document's child table.

    Args:
        doc: The Frappe document with an 'items' child table
        columns: List of column field names to display.
                 Default: ["item_name", "qty", "rate", "amount"]
        show_total: Whether to show a totals row at the bottom
        total_field: Document field name for the grand total
        currency_symbol: Currency symbol for formatting
    """
    if columns is None:
        columns = ["item_name", "qty", "rate", "amount"]

    items = doc.get("items", []) if hasattr(doc, "get") else []

    # Column headers (humanized)
    header_html = "<tr>"
    header_html += '<th class="ak-items-col-num">#</th>'
    for col in columns:
        label = col.replace("_", " ").title()
        header_html += f'<th class="ak-items-col-{col}">{label}</th>'
    header_html += "</tr>"

    # Rows
    rows_html = ""
    for idx, item in enumerate(items, 1):
        rows_html += "<tr>"
        rows_html += f'<td class="ak-items-col-num">{idx}</td>'
        for col in columns:
            val = item.get(col, "")
            if col in ("rate", "amount", "net_amount", "base_amount") and val:
                val = f"{currency_symbol}{frappe.utils.flt(val):,.2f}"
            elif col == "qty" and val:
                val = f"{frappe.utils.flt(val):g}"
            rows_html += f'<td class="ak-items-col-{col}">{frappe.utils.escape_html(str(val))}</td>'
        rows_html += "</tr>"

    # Total row
    total_html = ""
    if show_total and total_field:
        total_val = doc.get(total_field, 0) if hasattr(doc, "get") else 0
        colspan = len(columns)
        total_html = (
            f'<tr class="ak-items-total">'
            f'<td colspan="{colspan}"><strong>Total</strong></td>'
            f'<td><strong>{currency_symbol}{frappe.utils.flt(total_val):,.2f}</strong></td>'
            f'</tr>'
        )

    return Markup(
        f'<table class="ak-items-table">'
        f'<thead>{header_html}</thead>'
        f'<tbody>{rows_html}</tbody>'
        f'{f"<tfoot>{total_html}</tfoot>" if total_html else ""}'
        f'</table>'
    )


def ak_accept_decline(accept_label="Accept", decline_label="Decline"):
    """Render Accept and Decline buttons in a sticky bottom action bar.

    Args:
        accept_label: Text for the accept button
        decline_label: Text for the decline button
    """
    return Markup(
        f'<div class="ak-action-bar">'
        f'<div class="ak-action-bar-inner">'
        f'<button type="button" class="ak-decline-btn" data-action="Declined">'
        f'{frappe.utils.escape_html(decline_label)}</button>'
        f'<button type="button" class="ak-accept-btn" data-action="Accepted">'
        f'{frappe.utils.escape_html(accept_label)}</button>'
        f'</div>'
        f'</div>'
    )


def ak_submit_button(label="Submit"):
    """Render a submit button in a sticky bottom action bar.

    Args:
        label: Button text
    """
    return Markup(
        f'<div class="ak-action-bar">'
        f'<div class="ak-action-bar-inner">'
        f'<button type="button" class="ak-submit-btn" data-action="Submitted">'
        f'{frappe.utils.escape_html(label)}</button>'
        f'</div>'
        f'</div>'
    )
