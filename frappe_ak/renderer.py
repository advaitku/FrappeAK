"""Template rendering engine for AK Document Designer.

Renders an AK Document Template's HTML with a Frappe document context,
producing the final HTML that guests see on the shared page.
"""

import os
import json
import frappe
from frappe.utils import cint
from markupsafe import Markup
from jinja2.sandbox import SandboxedEnvironment

# Base CSS for PDF rendering (loaded once from document_styles.css)
_BASE_CSS_CACHE = None

_BODY_CSS = """
*, *::before, *::after { box-sizing: border-box; }
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    color: #1f2937; line-height: 1.6; margin: 0; padding: 0;
    -webkit-font-smoothing: antialiased;
}
.ak-shared-page { max-width: 900px; margin: 0 auto; padding: 24px 16px; }
.ak-document-form { background: #fff; border-radius: 12px; overflow: hidden; }
.ak-field { margin-bottom: 16px; }
.ak-field-label { display: block; font-size: 13px; font-weight: 600; color: #374151; margin-bottom: 4px; }
.ak-field-mandatory .ak-field-label::after { content: " *"; color: #ef4444; }
.ak-field-input {
    width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 6px;
    font-size: 14px; color: #1f2937; background: #fff; font-family: inherit;
}
.ak-field-readonly .ak-field-input { background: #f9fafb; color: #6b7280; }
.ak-field-input:disabled { background: #f9fafb; color: #6b7280; }
"""


def _get_base_css():
    """Load document_styles.css for embedding in PDF HTML."""
    global _BASE_CSS_CACHE
    if _BASE_CSS_CACHE is None:
        css_path = os.path.join(os.path.dirname(__file__), "public", "css", "document_styles.css")
        try:
            with open(css_path) as f:
                _BASE_CSS_CACHE = f.read()
        except FileNotFoundError:
            _BASE_CSS_CACHE = ""
    return _BASE_CSS_CACHE


def render_template(share_doc, for_preview=False):
    """Render a shared document's template into complete HTML.

    Args:
        share_doc: AK Document Share document (frappe.get_doc result)
        for_preview: If True, skip view logging and status updates

    Returns:
        dict with keys: html, cover_html, header_html, footer_html,
              custom_css, template_settings
    """
    template = frappe.get_doc("AK Document Template", share_doc.template)

    # Load the referenced document (or empty object for public forms)
    if template.is_public_form or not share_doc.reference_name:
        doc = frappe._dict()
    else:
        doc = frappe.get_doc(share_doc.reference_doctype, share_doc.reference_name)

    # Build Jinja2 context
    from frappe_ak.template_helpers import (
        ak_input, ak_textarea, ak_date, ak_datetime,
        ak_checkbox, ak_select, ak_field_table,
        ak_items_table, ak_accept_decline, ak_submit_button,
    )

    # Convert child table fields to list of dicts for ak_field_table
    template_fields = []
    for f in template.fields:
        template_fields.append({
            "field_name": f.field_name,
            "field_label": f.field_label,
            "field_type": f.field_type,
            "options": f.options,
            "is_existing_field": cint(f.is_existing_field),
            "is_editable": cint(f.is_editable),
            "is_mandatory": cint(f.is_mandatory),
            "default_value": f.default_value,
            "column": f.column,
        })

    context = {
        "doc": doc,
        "frappe": frappe._dict({
            "utils": frappe.utils,
            "format": frappe.format,
            "get_url": frappe.utils.get_url,
        }),
        "ak_input": ak_input,
        "ak_textarea": ak_textarea,
        "ak_date": ak_date,
        "ak_datetime": ak_datetime,
        "ak_checkbox": ak_checkbox,
        "ak_select": ak_select,
        "ak_field_table": lambda columns=1: ak_field_table(template_fields, columns=columns, doc=doc),
        "ak_items_table": lambda columns=None, show_total=True: ak_items_table(doc, columns=columns, show_total=show_total),
        "ak_accept_decline": ak_accept_decline,
        "ak_submit_button": ak_submit_button,
        "nowdate": frappe.utils.nowdate,
        "format_currency": frappe.utils.fmt_money,
        "share": share_doc,
        "template_fields": template_fields,
    }

    # Render each template section
    rendered = frappe._dict()
    rendered.html = _render_jinja(template.template_html or "", context)
    rendered.cover_html = _render_jinja(template.cover_page_html or "", context)
    rendered.header_html = _render_jinja(template.header_html or "", context)
    rendered.footer_html = _render_jinja(template.footer_html or "", context)
    rendered.custom_css = template.custom_css or ""

    rendered.template_settings = {
        "show_accept_decline": cint(template.show_accept_decline),
        "lock_after_submission": cint(template.lock_after_submission),
        "disable_access_after_submission": cint(template.disable_access_after_submission),
        "success_message": template.success_message or "",
        "page_format": template.page_format or "A4",
        "margins": {
            "top": template.top_margin or 15,
            "bottom": template.bottom_margin or 15,
            "left": template.left_margin or 15,
            "right": template.right_margin or 15,
        },
    }

    return rendered


def render_response(response_doc):
    """Re-render a template with submitted response values, all fields read-only.

    Args:
        response_doc: AK Document Response document (frappe.get_doc result)

    Returns:
        dict with keys: html, css
    """
    template = frappe.get_doc("AK Document Template", response_doc.template)

    # Load the original document or empty dict
    if template.is_public_form or not response_doc.reference_name:
        doc = frappe._dict()
    else:
        doc = frappe.get_doc(response_doc.reference_doctype, response_doc.reference_name)

    # Parse submitted field values
    response_data = {}
    if response_doc.response_data:
        response_data = json.loads(response_doc.response_data)

    # Build template field dicts with submitted values baked in, all forced read-only
    template_fields = []
    for f in template.fields:
        submitted_val = response_data.get(f.field_name)
        # Use submitted value if available, else fall back to doc value or default
        if submitted_val is not None:
            default_value = submitted_val
        elif not template.is_public_form and doc and f.is_existing_field:
            doc_val = doc.get(f.field_name) if hasattr(doc, "get") else None
            default_value = doc_val if doc_val is not None else (f.default_value or "")
        else:
            default_value = f.default_value or ""

        template_fields.append({
            "field_name": f.field_name,
            "field_label": f.field_label,
            "field_type": f.field_type,
            "options": f.options,
            "is_existing_field": cint(f.is_existing_field),
            "is_editable": 0,  # Force all read-only
            "is_mandatory": 0,
            "default_value": default_value,
            "column": f.column,
        })

    from frappe_ak.template_helpers import (
        ak_input, ak_textarea, ak_date, ak_datetime,
        ak_checkbox, ak_select, ak_field_table,
        ak_items_table,
    )

    # Wrap each helper to force editable=False and inject response values
    def _readonly_input(fieldname, label="", value="", placeholder="",
                        editable=True, mandatory=False, input_type="text"):
        val = response_data.get(fieldname, value)
        return ak_input(fieldname, label=label, value=val,
                        editable=False, mandatory=False, input_type=input_type)

    def _readonly_textarea(fieldname, label="", value="", rows=4,
                           editable=True, mandatory=False, placeholder=""):
        val = response_data.get(fieldname, value)
        return ak_textarea(fieldname, label=label, value=val, rows=rows,
                           editable=False, mandatory=False)

    def _readonly_date(fieldname, label="", value="", editable=True, mandatory=False):
        val = response_data.get(fieldname, value)
        return ak_date(fieldname, label=label, value=val,
                       editable=False, mandatory=False)

    def _readonly_datetime(fieldname, label="", value="", editable=True, mandatory=False):
        val = response_data.get(fieldname, value)
        return ak_datetime(fieldname, label=label, value=val,
                           editable=False, mandatory=False)

    def _readonly_checkbox(fieldname, label="", checked=False, editable=True):
        val = response_data.get(fieldname)
        if val is not None:
            checked = bool(int(val)) if str(val).isdigit() else bool(val)
        return ak_checkbox(fieldname, label=label, checked=checked, editable=False)

    def _readonly_select(fieldname, label="", options=None, value="",
                         editable=True, mandatory=False):
        val = response_data.get(fieldname, value)
        return ak_select(fieldname, label=label, options=options, value=val,
                         editable=False, mandatory=False)

    # Response badge instead of action buttons
    response_type = response_doc.response_type or "Submitted"
    badge_colors = {
        "Accepted": ("background:#f0fdf4;border-color:#86efac;color:#16a34a;", "Accepted"),
        "Declined": ("background:#fef2f2;border-color:#fca5a5;color:#dc2626;", "Declined"),
        "Submitted": ("background:#eff6ff;border-color:#93c5fd;color:#2563eb;", "Submitted"),
    }
    badge_style, badge_text = badge_colors.get(response_type, badge_colors["Submitted"])

    def _response_badge(*args, **kwargs):
        return Markup(
            f'<div style="text-align:center;padding:20px 16px;">'
            f'<span style="display:inline-block;padding:8px 24px;border-radius:8px;'
            f'font-size:14px;font-weight:600;border:1px solid;{badge_style}">'
            f'Response: {frappe.utils.escape_html(badge_text)}</span>'
            f'</div>'
        )

    context = {
        "doc": doc,
        "frappe": frappe._dict({
            "utils": frappe.utils,
            "format": frappe.format,
            "get_url": frappe.utils.get_url,
        }),
        "ak_input": _readonly_input,
        "ak_textarea": _readonly_textarea,
        "ak_date": _readonly_date,
        "ak_datetime": _readonly_datetime,
        "ak_checkbox": _readonly_checkbox,
        "ak_select": _readonly_select,
        "ak_field_table": lambda columns=1: ak_field_table(template_fields, columns=columns, doc=doc),
        "ak_items_table": lambda columns=None, show_total=True: ak_items_table(doc, columns=columns, show_total=show_total),
        "ak_accept_decline": _response_badge,
        "ak_submit_button": _response_badge,
        "nowdate": frappe.utils.nowdate,
        "format_currency": frappe.utils.fmt_money,
        "share": frappe._dict({"name": response_doc.document_share, "secret_key": ""}),
        "template_fields": template_fields,
    }

    html = _render_jinja(template.template_html or "", context)
    cover_html = _render_jinja(template.cover_page_html or "", context)
    header_html = _render_jinja(template.header_html or "", context)
    footer_html = _render_jinja(template.footer_html or "", context)

    # Combine all sections
    parts = []
    if cover_html:
        parts.append(f'<div class="ak-cover-page">{cover_html}</div>')
    if header_html:
        parts.append(f'<div class="ak-header">{header_html}</div>')
    parts.append(html)
    if footer_html:
        parts.append(f'<div class="ak-footer">{footer_html}</div>')

    return {
        "html": "\n".join(parts),
        "css": template.custom_css or "",
    }


def render_response_as_pdf(response_doc):
    """Render a submitted response as a PDF.

    Args:
        response_doc: AK Document Response document

    Returns:
        PDF bytes
    """
    result = render_response(response_doc)
    template = frappe.get_doc("AK Document Template", response_doc.template)

    css = (
        _BODY_CSS + "\n"
        + _get_base_css() + "\n"
        + (result["css"] or "") + "\n"
        + ".ak-action-bar { display:none !important; }\n"
    )
    full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>{result["html"]}</body>
</html>"""

    from frappe.utils.pdf import get_pdf
    return get_pdf(full_html, options={
        "page-size": template.page_format or "A4",
        "margin-top": f"{template.top_margin or 15}mm",
        "margin-bottom": f"{template.bottom_margin or 15}mm",
        "margin-left": f"{template.left_margin or 15}mm",
        "margin-right": f"{template.right_margin or 15}mm",
    })


def render_template_as_pdf(share_doc):
    """Render template to PDF bytes.

    Args:
        share_doc: AK Document Share document

    Returns:
        PDF bytes
    """
    rendered = render_template(share_doc, for_preview=True)

    full_html = _build_full_html(rendered)

    from frappe.utils.pdf import get_pdf
    return get_pdf(full_html, options={
        "page-size": rendered.template_settings.get("page_format", "A4"),
        "margin-top": f"{rendered.template_settings['margins']['top']}mm",
        "margin-bottom": f"{rendered.template_settings['margins']['bottom']}mm",
        "margin-left": f"{rendered.template_settings['margins']['left']}mm",
        "margin-right": f"{rendered.template_settings['margins']['right']}mm",
    })


def _build_full_html(rendered):
    """Build a complete HTML document from rendered parts, with full CSS for PDF."""
    parts = []

    if rendered.cover_html:
        parts.append(f'<div class="ak-cover-page">{rendered.cover_html}</div>')
        parts.append('<div class="ak-page-break"></div>')

    if rendered.header_html:
        parts.append(f'<div class="ak-header">{rendered.header_html}</div>')

    parts.append(f'<div class="ak-body">{rendered.html}</div>')

    if rendered.footer_html:
        parts.append(f'<div class="ak-footer">{rendered.footer_html}</div>')

    body = "\n".join(parts)

    # Include all CSS: body defaults + document_styles.css + template custom CSS
    # Hide the action bar and download button in PDF output
    css = (
        _BODY_CSS + "\n"
        + _get_base_css() + "\n"
        + (rendered.custom_css or "") + "\n"
        + ".ak-action-bar { display:none !important; }\n"
    )

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>{body}</body>
</html>"""


def _render_jinja(template_str, context):
    """Safely render a Jinja2 template string with context."""
    if not template_str or not template_str.strip():
        return ""

    try:
        env = SandboxedEnvironment()
        tmpl = env.from_string(template_str)
        return tmpl.render(**context)
    except Exception as e:
        frappe.log_error(title="Doc Designer AK", message=f"Template rendering error: {e}")
        return f'<div class="ak-error">Template rendering error: {frappe.utils.escape_html(str(e))}</div>'
