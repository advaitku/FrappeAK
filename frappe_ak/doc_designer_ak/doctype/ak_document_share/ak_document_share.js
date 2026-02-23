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

            // View Response button — when a response has been submitted
            if (["Submitted", "Accepted", "Declined"].includes(frm.doc.status)) {
                frm.add_custom_button(__("View Filled Document"), () => {
                    // Find the response linked to this share
                    frappe.call({
                        method: "frappe.client.get_list",
                        args: {
                            doctype: "AK Document Response",
                            filters: { document_share: frm.doc.name },
                            fields: ["name"],
                            limit_page_length: 1,
                            order_by: "creation desc",
                        },
                        callback(r) {
                            if (r.message && r.message.length) {
                                // Render and show inline
                                frappe.call({
                                    method: "frappe_ak.doc_api.render_response",
                                    args: { response_name: r.message[0].name },
                                    freeze: true,
                                    freeze_message: __("Rendering document..."),
                                    callback(r2) {
                                        if (r2.message) {
                                            _dd_show_filled_document(r2.message);
                                        }
                                    },
                                });
                            } else {
                                frappe.msgprint(__("No response found for this share."));
                            }
                        },
                    });
                }).addClass("btn-primary-dark");
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


function _dd_show_filled_document(data) {
    const d = new frappe.ui.Dialog({
        title: __("Filled Document"),
        size: "extra-large",
    });

    const badgeColors = {
        Accepted: { bg: "#f0fdf4", border: "#86efac", text: "#16a34a" },
        Declined: { bg: "#fef2f2", border: "#fca5a5", text: "#dc2626" },
        Submitted: { bg: "#eff6ff", border: "#93c5fd", text: "#2563eb" },
    };
    const bc = badgeColors[data.response_type] || badgeColors.Submitted;

    const submittedAt = data.submitted_at
        ? frappe.datetime.str_to_user(data.submitted_at)
        : "";

    let headerHtml =
        '<div style="display:flex;align-items:center;justify-content:space-between;' +
        'padding:12px 20px;background:#f9fafb;border-bottom:1px solid #e5e7eb;' +
        'font-size:13px;color:#6b7280;">' +
        '<span style="display:inline-flex;align-items:center;gap:8px;">' +
        '<span style="display:inline-block;padding:4px 12px;border-radius:6px;' +
        "font-weight:600;font-size:12px;border:1px solid " +
        bc.border + ";background:" + bc.bg + ";color:" + bc.text + ';">' +
        frappe.utils.escape_html(data.response_type) +
        "</span>";

    if (data.reference_name) {
        headerHtml += " &mdash; " + frappe.utils.escape_html(data.reference_name);
    }
    headerHtml += "</span>";

    if (submittedAt) {
        headerHtml +=
            '<span style="font-size:12px;">' + __("Submitted") + " " + submittedAt + "</span>";
    }
    headerHtml += "</div>";

    d.$body.css({ padding: 0, overflow: "auto", "max-height": "75vh" });
    d.$body.html(
        headerHtml +
        "<style>" + (data.css || "") +
        ".ak-action-bar { display:none !important; }" +
        "</style>" +
        '<div style="background:#fff;padding:40px;">' +
        (data.html || "") +
        "</div>"
    );

    d.show();
}
