frappe.ui.form.on("AK Document Share", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.share_url) {
            // Show share URL prominently
            frm.set_intro(
                `<strong>Share URL:</strong> <a href="${frm.doc.share_url}" target="_blank">${frm.doc.share_url}</a>
                 <button class="btn btn-xs btn-default ml-2" onclick="navigator.clipboard.writeText('${frm.doc.share_url}').then(() => frappe.show_alert('Copied!'))">
                 Copy Link</button>`,
                "blue"
            );

            // Add action buttons
            if (frm.doc.is_active && frm.doc.status !== "Expired") {
                frm.add_custom_button(__("Send Email"), () => {
                    if (!frm.doc.recipient_email) {
                        frappe.prompt(
                            { fieldtype: "Data", label: "Recipient Email", fieldname: "email", options: "Email", reqd: 1 },
                            (values) => {
                                frm.set_value("recipient_email", values.email);
                                frm.save().then(() => {
                                    frm.call("send_email").then(() => {
                                        frappe.show_alert({ message: __("Email sent!"), indicator: "green" });
                                        frm.reload_doc();
                                    });
                                });
                            },
                            __("Enter Recipient Email")
                        );
                    } else {
                        frm.call("send_email").then(() => {
                            frappe.show_alert({ message: __("Email sent!"), indicator: "green" });
                            frm.reload_doc();
                        });
                    }
                }, __("Actions"));

                frm.add_custom_button(__("Revoke Link"), () => {
                    frappe.confirm(
                        __("Are you sure you want to revoke this link? Recipients will no longer be able to access the document."),
                        () => {
                            frm.call("revoke").then(() => {
                                frappe.show_alert({ message: __("Link revoked"), indicator: "orange" });
                                frm.reload_doc();
                            });
                        }
                    );
                }, __("Actions"));

                frm.add_custom_button(__("Preview"), () => {
                    window.open(frm.doc.share_url, "_blank");
                }, __("Actions"));
            }
        }
    },

    template(frm) {
        if (frm.doc.template) {
            frappe.db.get_value("AK Document Template", frm.doc.template, "reference_doctype")
                .then((r) => {
                    if (r.message) {
                        frm.set_value("reference_doctype", r.message.reference_doctype);
                    }
                });
        }
    },
});
