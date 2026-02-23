import frappe
from frappe.utils import now_datetime, add_days, get_datetime


def expire_shares():
    """Find all active shares past expires_at and mark them expired."""
    expired = frappe.get_all(
        "AK Document Share",
        filters={
            "is_active": 1,
            "expires_at": ["<", now_datetime()],
            "status": ["not in", ["Expired"]],
        },
        pluck="name",
    )

    for name in expired:
        frappe.db.set_value("AK Document Share", name, {
            "is_active": 0,
            "status": "Expired",
        }, update_modified=False)

    if expired:
        frappe.db.commit()
        frappe.logger().info(f"Doc Designer AK: Expired {len(expired)} shares")


def send_reminders():
    """Send reminder emails for shares that haven't received a response.

    Checks all active shares where:
    - Template has reminder_days > 0
    - Email was sent
    - No reminder has been sent yet
    - Share was created more than reminder_days ago
    - Status is still Active or Viewed (no submission)
    """
    # Get templates with reminders configured
    templates = frappe.get_all(
        "AK Document Template",
        filters={
            "is_active": 1,
            "reminder_days": [">", 0],
        },
        fields=["name", "reminder_days"],
    )

    if not templates:
        return

    reminder_count = 0

    for tmpl in templates:
        cutoff = add_days(now_datetime(), -tmpl.reminder_days)

        shares = frappe.get_all(
            "AK Document Share",
            filters={
                "template": tmpl.name,
                "is_active": 1,
                "email_sent": 1,
                "reminder_sent": 0,
                "status": ["in", ["Active", "Viewed"]],
                "creation": ["<", cutoff],
                "recipient_email": ["is", "set"],
            },
            fields=["name", "recipient_email"],
        )

        for share in shares:
            try:
                from frappe_ak.email_utils import send_document_email
                send_document_email(share.name)

                frappe.db.set_value("AK Document Share", share.name, {
                    "reminder_sent": 1,
                    "reminder_sent_at": now_datetime(),
                }, update_modified=False)

                reminder_count += 1
            except Exception:
                frappe.log_error(
                    f"Reminder send failed for share {share.name}",
                    "Doc Designer AK Reminder Error",
                )

    if reminder_count:
        frappe.db.commit()
        frappe.logger().info(f"Doc Designer AK: Sent {reminder_count} reminders")
