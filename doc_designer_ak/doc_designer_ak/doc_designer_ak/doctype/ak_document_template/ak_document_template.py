import frappe
from frappe import _
from frappe.model.document import Document


class AKDocumentTemplate(Document):
    def validate(self):
        if not self.template_html and not self.is_public_form:
            frappe.throw(_("Template HTML is required"))

        if self.auto_send_on and not self.auto_send_to_field:
            frappe.throw(_("Auto Send To Field is required when Auto Send On is set"))

        if self.expires_in_days and self.expires_in_days < 1:
            frappe.throw(_("Expires In Days must be at least 1"))

    def on_update(self):
        # Clear any cached template data
        frappe.cache.delete_value(f"ak_template_{self.name}")
