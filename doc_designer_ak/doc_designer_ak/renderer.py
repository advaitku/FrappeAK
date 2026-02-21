"""Template rendering engine for AK Document Designer.

Renders an AK Document Template's HTML with a Frappe document context,
producing the final HTML that guests see on the shared page.
"""

import frappe
from frappe.utils import cint
from jinja2.sandbox import SandboxedEnvironment


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
    from doc_designer_ak.template_helpers import (
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
    """Build a complete HTML document from rendered parts."""
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

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{rendered.custom_css}</style>
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
        frappe.log_error(f"Template rendering error: {e}", "Doc Designer AK")
        return f'<div class="ak-error">Template rendering error: {frappe.utils.escape_html(str(e))}</div>'
