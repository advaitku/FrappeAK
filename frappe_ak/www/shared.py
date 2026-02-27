"""Guest-accessible page for viewing shared documents.

URL: /shared?key=<secret_key>

This page renders the shared document template with interactive form fields.
No login required — access is controlled via the secret key and expiry.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime

no_cache = True


def get_context(context):
    # Override base template for a clean standalone page
    context.base_template_path = "templates/includes/shared_base.html"
    context.no_breadcrumbs = True
    context.show_sidebar = False
    try:
        context.csrf_token = frappe.sessions.get_csrf_token()
    except Exception:
        context.csrf_token = frappe.generate_hash()

    key = frappe.form_dict.get("key")
    if not key:
        context.error = _("No document key provided")
        context.error_code = "missing_key"
        return

    share = frappe.db.get_value(
        "AK Document Share",
        {"secret_key": key},
        ["name", "template", "reference_doctype", "reference_name",
         "is_active", "expires_at", "status", "is_locked"],
        as_dict=True,
    )

    if not share:
        context.error = _("Document not found or link is invalid")
        context.error_code = "not_found"
        return

    # Check if expired (by status or by expiry datetime)
    is_expired = share.status == "Expired"
    if not is_expired and share.expires_at:
        is_expired = get_datetime(share.expires_at) < now_datetime()

    if is_expired:
        # Auto-expire if not already
        if share.is_active or share.status != "Expired":
            frappe.db.set_value("AK Document Share", share.name, {
                "is_active": 0,
                "status": "Expired",
            })
        context.error = _("This link has expired")
        context.error_code = "expired"
        return

    if not share.is_active:
        context.error = _("This document link is no longer active")
        context.error_code = "inactive"
        return

    # Check template settings
    template = frappe.get_doc("AK Document Template", share.template)

    if share.is_locked:
        if template.disable_access_after_submission:
            context.error = _("This document has already been submitted and is no longer accessible")
            context.error_code = "submitted"
            return
        else:
            context.is_locked = True

    # Log the view and notify sender
    share_doc = frappe.get_doc("AK Document Share", share.name)
    share_doc.log_view()
    frappe.db.commit()

    from frappe_ak.doc_api import notify_on_view
    notify_on_view(share.name)

    # Render the template
    from frappe_ak.renderer import render_template
    rendered = render_template(share_doc)

    context.rendered_html = rendered.html
    context.cover_html = rendered.cover_html
    context.header_html = rendered.header_html
    context.footer_html = rendered.footer_html
    context.custom_css = rendered.custom_css
    context.template_settings = rendered.template_settings
    context.secret_key = key
    context.share_name = share.name
    context.is_locked = share.is_locked
    context.title = template.template_name

    # Format expiry for footer
    from frappe.utils import formatdate
    context.expires_at_formatted = formatdate(share.expires_at) if share.expires_at else ""

    # Load settings for branding
    if frappe.db.exists("DocType", "AK Document Settings"):
        settings = frappe.get_single("AK Document Settings")
        context.company_name = settings.company_name or ""
        context.company_logo = settings.company_logo or ""
        context.footer_text = settings.shared_page_footer_text or ""
    else:
        context.company_name = ""
        context.company_logo = ""
        context.footer_text = ""
