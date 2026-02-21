/**
 * Adds "Share via Document Designer" button to all Frappe forms
 * that have an AK Document Template configured for their DocType.
 */
frappe.ui.form.on_doctype_event("*", "refresh", function (frm) {
    if (frm.is_new()) return;

    // Check if templates exist for this DocType
    frappe.xcall(
        "frappe.client.get_count",
        {
            doctype: "AK Document Template",
            filters: {
                reference_doctype: frm.doc.doctype,
                is_active: 1,
            },
        }
    ).then((count) => {
        if (!count) return;

        // Remove existing button to avoid duplicates
        frm.remove_custom_button(__("Share via Document Designer"), __("Menu"));

        frm.add_custom_button(
            __("Share via Document Designer"),
            () => showShareDialog(frm),
            __("Menu")
        );
    });
});

function showShareDialog(frm) {
    // Fetch available templates for this DocType
    frappe.xcall("frappe.client.get_list", {
        doctype: "AK Document Template",
        filters: {
            reference_doctype: frm.doc.doctype,
            is_active: 1,
        },
        fields: ["name", "template_name", "expires_in_days"],
    }).then((templates) => {
        if (!templates || !templates.length) {
            frappe.msgprint(__("No active templates found for {0}", [frm.doc.doctype]));
            return;
        }

        const templateOptions = templates.map((t) => t.name);
        const defaultExpiry = templates[0].expires_in_days || 7;

        const d = new frappe.ui.Dialog({
            title: __("Share Document"),
            fields: [
                {
                    fieldname: "template",
                    fieldtype: "Select",
                    label: __("Template"),
                    options: templateOptions.join("\n"),
                    default: templateOptions[0],
                    reqd: 1,
                    onchange: function () {
                        const selected = templates.find((t) => t.name === d.get_value("template"));
                        if (selected) {
                            d.set_value("expires_in_days", selected.expires_in_days || 7);
                        }
                    },
                },
                {
                    fieldname: "recipient_email",
                    fieldtype: "Data",
                    label: __("Recipient Email"),
                    options: "Email",
                },
                {
                    fieldname: "expires_in_days",
                    fieldtype: "Int",
                    label: __("Expires In (Days)"),
                    default: defaultExpiry,
                    reqd: 1,
                },
                {
                    fieldname: "send_email",
                    fieldtype: "Check",
                    label: __("Send Email Now"),
                    default: 0,
                },
            ],
            primary_action_label: __("Create Share Link"),
            primary_action: (values) => {
                d.hide();
                frappe.call({
                    method: "doc_designer_ak.api.create_share",
                    args: {
                        template: values.template,
                        reference_doctype: frm.doc.doctype,
                        reference_name: frm.doc.name,
                        recipient_email: values.recipient_email || "",
                        expires_in_days: values.expires_in_days,
                    },
                    callback: (r) => {
                        if (r.message) {
                            const shareUrl = r.message.share_url;

                            if (values.send_email && values.recipient_email) {
                                frappe.call({
                                    method: "doc_designer_ak.api.send_document_email",
                                    args: { share_name: r.message.name },
                                    callback: () => {
                                        showShareResult(shareUrl, true);
                                    },
                                });
                            } else {
                                showShareResult(shareUrl, false);
                            }
                        }
                    },
                });
            },
        });

        d.show();
    });
}

function showShareResult(url, emailSent) {
    const msg = emailSent
        ? __("Share link created and email sent!")
        : __("Share link created!");

    const d = new frappe.ui.Dialog({
        title: msg,
        fields: [
            {
                fieldname: "share_url",
                fieldtype: "Data",
                label: __("Share URL"),
                default: url,
                read_only: 1,
            },
        ],
        primary_action_label: __("Copy Link"),
        primary_action: () => {
            navigator.clipboard.writeText(url).then(() => {
                frappe.show_alert({ message: __("Link copied!"), indicator: "green" });
                d.hide();
            });
        },
    });

    d.show();

    // Also add a "Preview" button
    d.$wrapper.find(".modal-footer").prepend(
        `<button class="btn btn-default btn-sm" onclick="window.open('${url}', '_blank')">${__("Preview")}</button>`
    );
}
