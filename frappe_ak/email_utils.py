"""Email utilities for AK Document Designer."""

import frappe
from frappe import _
from frappe.utils import now_datetime
from jinja2.sandbox import SandboxedEnvironment


def send_document_email(share_name):
    """Send the document email for a given share.

    Renders the email template with merge fields, includes the share URL,
    and optionally attaches a PDF copy of the document.
    """
    share = frappe.get_doc("AK Document Share", share_name)
    template = frappe.get_doc("AK Document Template", share.template)

    if not share.recipient_email:
        frappe.throw(_("No recipient email set on this share"))

    # Load document for merge fields
    if share.reference_name:
        doc = frappe.get_doc(share.reference_doctype, share.reference_name)
    else:
        doc = frappe._dict()

    # Build context for email templates
    context = {
        "doc": doc,
        "share_url": share.share_url,
        "recipient_email": share.recipient_email,
        "frappe": frappe._dict({"utils": frappe.utils}),
        "nowdate": frappe.utils.nowdate,
    }

    # Render subject and body
    subject = _render_jinja(template.email_subject or "", context) or f"Document: {share.reference_name or template.template_name}"
    body = _render_jinja(template.email_body_html or "", context) or _default_email_body(share, template)

    attachments = []
    if template.attach_pdf and share.reference_name:
        from frappe_ak.renderer import render_template_as_pdf
        pdf_bytes = render_template_as_pdf(share)
        filename = f"{share.reference_name or template.template_name}.pdf"
        attachments.append({
            "fname": filename,
            "fcontent": pdf_bytes,
        })

    settings = frappe.get_single("AK Document Settings") if frappe.db.exists("DocType", "AK Document Settings") else None
    sender = (settings.default_sender_email if settings and settings.default_sender_email else None)

    frappe.sendmail(
        recipients=[share.recipient_email],
        subject=subject,
        message=body,
        attachments=attachments or None,
        sender=sender,
        reference_doctype="AK Document Share",
        reference_name=share.name,
        now=True,
    )

    share.db_set("email_sent", 1)
    share.db_set("email_sent_at", now_datetime())


def _default_email_body(share, template):
    """Generate a default email body when no template is configured."""
    return f"""
    <p>You have been sent a document for your review.</p>
    <p><a href="{share.share_url}" style="display:inline-block;padding:10px 20px;
    background:#4F46E5;color:#fff;text-decoration:none;border-radius:6px;">
    Open Document</a></p>
    <p>This link will expire on {frappe.utils.format_datetime(share.expires_at)}.</p>
    """


def _render_jinja(template_str, context):
    """Render a Jinja2 string with context."""
    if not template_str or not template_str.strip():
        return ""
    try:
        env = SandboxedEnvironment()
        tmpl = env.from_string(template_str)
        return tmpl.render(**context)
    except Exception as e:
        frappe.log_error(f"Email template render error: {e}", "Doc Designer AK")
        return ""
