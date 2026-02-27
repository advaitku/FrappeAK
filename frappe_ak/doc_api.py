import frappe
import json
from frappe import _


@frappe.whitelist(allow_guest=True)
def submit_response(secret_key, response_type, field_values):
    """Submit a response to a shared document.

    Args:
        secret_key: The secret key from the share URL
        response_type: 'Submitted', 'Accepted', or 'Declined'
        field_values: JSON string of {field_name: value} pairs
    """
    if isinstance(field_values, str):
        field_values = json.loads(field_values)

    share = frappe.db.get_value(
        "AK Document Share",
        {"secret_key": secret_key},
        ["name", "template", "reference_doctype", "reference_name",
         "is_active", "expires_at", "status", "is_locked"],
        as_dict=True,
    )

    if not share:
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)

    if not share.is_active:
        frappe.throw(_("This document link is no longer active"))

    if share.is_locked:
        frappe.throw(_("This document has already been submitted"))

    from frappe.utils import now_datetime, get_datetime
    is_expired = share.status == "Expired"
    if not is_expired and share.expires_at:
        is_expired = get_datetime(share.expires_at) < now_datetime()
    if is_expired:
        frappe.throw(_("This link has expired"))

    template = frappe.get_doc("AK Document Template", share.template)

    # Validate mandatory fields
    for tf in template.fields:
        if tf.is_mandatory and tf.is_editable:
            val = field_values.get(tf.field_name)
            if val is None or val == "":
                frappe.throw(_("Field '{0}' is mandatory").format(tf.field_label or tf.field_name))

    # Create response record
    response = frappe.get_doc({
        "doctype": "AK Document Response",
        "document_share": share.name,
        "template": share.template,
        "reference_doctype": share.reference_doctype,
        "reference_name": share.reference_name,
        "response_type": response_type,
        "submitted_at": now_datetime(),
        "ip_address": frappe.local.request_ip,
        "user_agent": frappe.request.headers.get("User-Agent", "")[:500] if frappe.request else "",
        "response_data": json.dumps(field_values, default=str),
    })

    fields_updated = {}

    if template.is_public_form:
        # Public form mode: create a new record
        new_doc = frappe.new_doc(share.reference_doctype)
        for tf in template.fields:
            if tf.is_existing_field and tf.field_name in field_values:
                new_doc.set(tf.field_name, field_values[tf.field_name])
        new_doc.insert(ignore_permissions=True)
        response.created_new_record = new_doc.name
    else:
        # Document mode: update existing fields
        if share.reference_name:
            doc = frappe.get_doc(share.reference_doctype, share.reference_name)
            for tf in template.fields:
                if tf.is_existing_field and tf.is_editable and tf.field_name in field_values:
                    old_val = doc.get(tf.field_name)
                    new_val = field_values[tf.field_name]
                    if str(old_val) != str(new_val):
                        doc.set(tf.field_name, new_val)
                        fields_updated[tf.field_name] = {
                            "old": str(old_val),
                            "new": str(new_val),
                        }
            if fields_updated:
                doc.flags.ignore_permissions = True
                doc.save()

    response.fields_updated_on_original = json.dumps(fields_updated, default=str) if fields_updated else ""
    response.insert(ignore_permissions=True)

    # Update share status using db_set to avoid Frappe's reserved property conflicts
    update_fields = {
        "status": response_type if response_type in ("Accepted", "Declined") else "Submitted",
        "submitted_at": now_datetime(),
    }
    if template.lock_after_submission:
        update_fields["is_locked"] = 1

    frappe.db.set_value("AK Document Share", share.name, update_fields)
    share_doc = frappe.get_doc("AK Document Share", share.name)

    # Execute response actions — update fields on the original document based on response type
    actions_applied = {}
    if share.reference_name and not template.is_public_form and template.response_actions:
        action_doc = frappe.get_doc(share.reference_doctype, share.reference_name)
        for action in template.response_actions:
            if action.response_type == response_type:
                old_val = action_doc.get(action.field_name)
                action_doc.set(action.field_name, action.value)
                actions_applied[action.field_name] = {
                    "old": str(old_val) if old_val is not None else "",
                    "new": action.value,
                }
        if actions_applied:
            action_doc.flags.ignore_permissions = True
            action_doc.save()

    # Auto-attach filled document as PDF to the original record
    if template.attach_pdf_on_submission and share.reference_name and not template.is_public_form:
        try:
            from frappe_ak.renderer import render_response_as_pdf
            pdf_bytes = render_response_as_pdf(response)
            file_name = f"{share.reference_name}-{response_type}-{response.name}.pdf"
            _file = frappe.get_doc({
                "doctype": "File",
                "file_name": file_name,
                "attached_to_doctype": share.reference_doctype,
                "attached_to_name": share.reference_name,
                "is_private": 1,
                "content": pdf_bytes,
            })
            _file.save(ignore_permissions=True)

            # Save file URL on response and share for easy access
            frappe.db.set_value("AK Document Response", response.name, "attached_pdf", _file.file_url)
            frappe.db.set_value("AK Document Share", share.name, "attached_pdf", _file.file_url)
        except Exception:
            frappe.log_error(
                f"PDF attachment failed for response {response.name}",
                "Doc Designer AK PDF Error",
            )

    # Audit trail: add comment on the original document
    has_changes = fields_updated or actions_applied
    if has_changes and share.reference_name and not template.is_public_form:
        changes_list = []
        for fname, vals in fields_updated.items():
            changes_list.append(f"<li><strong>{fname}</strong>: {vals['old']} → {vals['new']}</li>")
        for fname, vals in actions_applied.items():
            changes_list.append(f"<li><strong>{fname}</strong>: {vals['old']} → {vals['new']} <em>(response action)</em></li>")
        comment_html = (
            f"<p>Fields updated via Document Designer ({share.name}):</p>"
            f"<ul>{''.join(changes_list)}</ul>"
            f"<p>Response: <strong>{response_type}</strong>"
            f"{' by ' + (share_doc.recipient_email or 'anonymous')}</p>"
        )
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": share.reference_doctype,
            "reference_name": share.reference_name,
            "content": comment_html,
        }).insert(ignore_permissions=True)
    elif template.is_public_form and response.created_new_record:
        frappe.get_doc({
            "doctype": "Comment",
            "comment_type": "Info",
            "reference_doctype": share.reference_doctype,
            "reference_name": response.created_new_record,
            "content": f"<p>Record created via Document Designer ({share.name})</p>",
        }).insert(ignore_permissions=True)

    # Notify sender
    if template.notify_on_response and share_doc.shared_by:
        _notify_sender(
            share_doc,
            subject=_("{0} response on {1}").format(response_type, share.reference_name or template.template_name),
            message=_("{0} responded with <strong>{1}</strong> on document {2} via template {3}").format(
                share_doc.recipient_email or "Recipient",
                response_type,
                share.reference_name or "Public Form",
                template.template_name,
            ),
        )

    frappe.db.commit()

    success_message = template.success_message or _("Your response has been recorded. Thank you!")
    return {"success": True, "message": success_message}


@frappe.whitelist()
def create_share(template, reference_doctype=None, reference_name=None,
                 recipient_email=None, expires_in_days=None):
    """Create a new AK Document Share and return the share URL."""
    share = frappe.get_doc({
        "doctype": "AK Document Share",
        "template": template,
        "reference_doctype": reference_doctype,
        "reference_name": reference_name,
        "recipient_email": recipient_email,
    })

    if expires_in_days:
        from frappe.utils import add_days, now_datetime
        share.expires_at = add_days(now_datetime(), int(expires_in_days))

    share.insert()
    frappe.db.commit()

    return {
        "name": share.name,
        "share_url": share.share_url,
        "secret_key": share.secret_key,
        "expires_at": str(share.expires_at),
    }


@frappe.whitelist()
def send_document_email(share_name):
    """Send the document email for a given share."""
    from frappe_ak.email_utils import send_document_email as _send
    _send(share_name)
    return {"success": True}


@frappe.whitelist(allow_guest=True)
def download_pdf(secret_key):
    """Download the shared document as a PDF. Guest-accessible via secret key."""
    share = frappe.db.get_value(
        "AK Document Share",
        {"secret_key": secret_key},
        ["name", "template", "reference_doctype", "reference_name",
         "is_active", "expires_at"],
        as_dict=True,
    )
    if not share:
        frappe.throw(_("Document not found"), frappe.DoesNotExistError)

    from frappe.utils import now_datetime, get_datetime
    if not share.is_active:
        frappe.throw(_("This document link is no longer active"))
    is_expired = share.expires_at and get_datetime(share.expires_at) < now_datetime()
    if is_expired:
        frappe.throw(_("This link has expired"))

    share_doc = frappe.get_doc("AK Document Share", share.name)
    from frappe_ak.renderer import render_template_as_pdf
    pdf_bytes = render_template_as_pdf(share_doc)

    file_name = f"{share.reference_name or 'document'}.pdf"
    frappe.local.response.filename = file_name
    frappe.local.response.filecontent = pdf_bytes
    frappe.local.response.type = "download"


@frappe.whitelist()
def get_preview_html(share_name):
    """Return rendered HTML for preview ('as recipient sees it')."""
    from frappe_ak.renderer import render_template
    share = frappe.get_doc("AK Document Share", share_name)
    html = render_template(share, for_preview=True)
    return {"html": html}


@frappe.whitelist()
def render_response(response_name):
    """Render a submitted response as a filled-in document.

    Returns the template re-rendered with all submitted values shown read-only.

    Args:
        response_name: Name of the AK Document Response record
    """
    response_doc = frappe.get_doc("AK Document Response", response_name)
    response_doc.check_permission("read")

    from frappe_ak.renderer import render_response as _render_response
    result = _render_response(response_doc)

    return {
        "html": result["html"],
        "css": result["css"],
        "response_type": response_doc.response_type,
        "submitted_at": str(response_doc.submitted_at) if response_doc.submitted_at else "",
        "reference_name": response_doc.reference_name or "",
        "template": response_doc.template,
    }


@frappe.whitelist()
def preview_template(template_name, reference_name=None):
    """Render a template preview directly (no share required).

    Args:
        template_name: Name of the AK Document Template
        reference_name: Optional document name to render with real data
    """
    from frappe_ak.template_helpers import (
        ak_input, ak_textarea, ak_date, ak_datetime,
        ak_checkbox, ak_select, ak_field_table,
        ak_items_table, ak_accept_decline, ak_submit_button,
    )
    from jinja2.sandbox import SandboxedEnvironment
    from frappe.utils import cint

    template = frappe.get_doc("AK Document Template", template_name)

    # Load document or empty dict
    if reference_name and template.reference_doctype:
        doc = frappe.get_doc(template.reference_doctype, reference_name)
    else:
        doc = frappe._dict()

    # Build field dicts
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
        "share": frappe._dict({"name": "PREVIEW", "secret_key": "preview"}),
        "template_fields": template_fields,
    }

    try:
        env = SandboxedEnvironment()
        rendered_html = env.from_string(template.template_html or "").render(**context)
    except Exception as e:
        rendered_html = f'<div style="color:#dc2626;padding:16px;background:#fef2f2;border-radius:8px;margin:8px 0;">' \
                        f'<strong>Template Error:</strong> {frappe.utils.escape_html(str(e))}</div>'

    css = template.custom_css or ""

    return {
        "html": rendered_html,
        "css": css,
    }


@frappe.whitelist()
def get_doctype_fields(doctype_name):
    """Return all fields for a DocType, grouped by type.

    Used by the Field Explorer on the template form.
    """
    meta = frappe.get_meta(doctype_name)
    fields = []

    for f in meta.fields:
        if f.fieldtype in ("Section Break", "Column Break", "Tab Break"):
            continue
        fields.append({
            "fieldname": f.fieldname,
            "label": f.label or f.fieldname,
            "fieldtype": f.fieldtype,
            "options": f.options or "",
            "reqd": f.reqd or 0,
            "read_only": f.read_only or 0,
            "is_child_table": 1 if f.fieldtype == "Table" else 0,
        })

    # Also get child table fields
    child_tables = {}
    for f in meta.fields:
        if f.fieldtype == "Table" and f.options:
            child_meta = frappe.get_meta(f.options)
            child_fields = []
            for cf in child_meta.fields:
                if cf.fieldtype in ("Section Break", "Column Break", "Tab Break"):
                    continue
                child_fields.append({
                    "fieldname": cf.fieldname,
                    "label": cf.label or cf.fieldname,
                    "fieldtype": cf.fieldtype,
                    "options": cf.options or "",
                })
            child_tables[f.fieldname] = {
                "doctype": f.options,
                "label": f.label or f.fieldname,
                "fields": child_fields,
            }

    return {
        "fields": fields,
        "child_tables": child_tables,
    }


def notify_on_view(share_name):
    """Send a notification to the sender when a document is viewed.

    Called from www/shared.py after logging the view.
    """
    share = frappe.get_doc("AK Document Share", share_name)
    template = frappe.get_doc("AK Document Template", share.template)

    if not template.notify_on_view or not share.shared_by:
        return

    # Only notify on first view to avoid spam
    if share.view_count > 1:
        return

    _notify_sender(
        share,
        subject=_("Document viewed: {0}").format(share.reference_name or template.template_name),
        message=_("{0} opened the document {1} (template: {2})").format(
            share.recipient_email or "Recipient",
            share.reference_name or "Public Form",
            template.template_name,
        ),
    )


def _notify_sender(share_doc, subject, message):
    """Create a Frappe notification and send email to the share sender."""
    try:
        # In-app notification
        frappe.publish_realtime(
            "eval_js",
            f'frappe.show_alert({{message: "{frappe.utils.escape_html(subject)}", indicator: "blue"}});',
            user=share_doc.shared_by,
        )

        # Email notification
        frappe.sendmail(
            recipients=[share_doc.shared_by],
            subject=subject,
            message=f"<p>{message}</p>"
                    f"<p><a href='{frappe.utils.get_url()}/app/ak-document-share/{share_doc.name}'>"
                    f"View Share Details</a></p>",
            now=True,
        )
    except Exception:
        frappe.log_error(
            f"Notification failed for share {share_doc.name}",
            "Doc Designer AK Notification Error",
        )


def check_auto_send(doc, method):
    """Check if any AK Document Template has auto-send configured for this event."""
    event_map = {
        "after_insert": "on_insert",
        "on_update": "on_update",
        "on_submit": "on_submit",
    }
    event_name = event_map.get(method)
    if not event_name:
        return

    templates = frappe.get_all(
        "AK Document Template",
        filters={
            "is_active": 1,
            "auto_send_on": event_name,
            "reference_doctype": doc.doctype,
        },
        fields=["name", "auto_send_to_field", "expires_in_days"],
    )

    for tmpl in templates:
        recipient = doc.get(tmpl.auto_send_to_field) if tmpl.auto_send_to_field else None
        if not recipient:
            continue

        try:
            result = create_share(
                template=tmpl.name,
                reference_doctype=doc.doctype,
                reference_name=doc.name,
                recipient_email=recipient,
                expires_in_days=tmpl.expires_in_days,
            )
            send_document_email(result["name"])
        except Exception:
            frappe.log_error(
                f"Auto-send failed for {doc.doctype} {doc.name} with template {tmpl.name}",
                "Doc Designer AK Auto-Send Error",
            )
