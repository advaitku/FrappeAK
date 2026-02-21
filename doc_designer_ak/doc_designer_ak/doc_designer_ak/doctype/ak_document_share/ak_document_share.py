import frappe
import uuid
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, now_datetime, get_datetime, get_url


class AKDocumentShare(Document):
    def before_insert(self):
        if not self.secret_key:
            self.secret_key = str(uuid.uuid4())

        if not self.shared_by:
            self.shared_by = frappe.session.user

        # Auto-set reference_doctype from template
        if self.template and not self.reference_doctype:
            self.reference_doctype = frappe.db.get_value(
                "AK Document Template", self.template, "reference_doctype"
            )

        # Compute expires_at from template if not set
        if not self.expires_at:
            expires_in_days = frappe.db.get_value(
                "AK Document Template", self.template, "expires_in_days"
            ) or 7
            self.expires_at = add_days(now_datetime(), int(expires_in_days))

        # Compute share URL
        self.share_url = f"{get_url()}/shared?key={self.secret_key}"

    def validate(self):
        if not self.template:
            frappe.throw(_("Template is required"))

        template = frappe.get_doc("AK Document Template", self.template)

        # Public forms don't require a reference_name
        if not template.is_public_form and not self.reference_name:
            frappe.throw(_("Reference Name is required for non-public-form templates"))

        if self.expires_at and get_datetime(self.expires_at) < now_datetime():
            frappe.throw(_("Expiry date must be in the future"))

    @frappe.whitelist()
    def send_email(self):
        """Send the document email."""
        from doc_designer_ak.email_utils import send_document_email
        send_document_email(self.name)
        self.reload()

    @frappe.whitelist()
    def revoke(self):
        """Revoke this share link."""
        self.is_active = 0
        self.status = "Expired"
        self.save(ignore_permissions=True)

    def log_view(self, request=None):
        """Log a view of this shared document."""
        template = frappe.db.get_value(
            "AK Document Template", self.template, "track_opens"
        )

        if template:
            frappe.get_doc({
                "doctype": "AK Document View Log",
                "document_share": self.name,
                "viewed_at": now_datetime(),
                "ip_address": frappe.local.request_ip if frappe.local.request else "",
                "user_agent": (
                    frappe.request.headers.get("User-Agent", "")[:500]
                    if frappe.request else ""
                ),
            }).insert(ignore_permissions=True)

        # Update view count and status
        self.view_count = (self.view_count or 0) + 1
        self.last_viewed_at = now_datetime()
        if self.status == "Active":
            self.status = "Viewed"
        self.flags.ignore_permissions = True
        self.save()
