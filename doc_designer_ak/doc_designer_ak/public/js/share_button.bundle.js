/**
 * Adds "Share via Doc Designer" button to all Frappe forms
 * that have an AK Document Template configured for their DocType.
 */

let _dd_template_cache = {};
const _DD_SKIP_DOCTYPES = [
    "AK Document Template", "AK Document Share",
    "AK Document Response", "AK Document View Log",
    "AK Document Settings",
];

// Use the jQuery form-refresh event — the same reliable pattern
// that automation_ak uses. frappe.ui.form.on_doctype_event does
// not exist in Frappe v16.
$(document).on("form-refresh", function (e, frm) {
    if (!frm || !frm.doc || frm.doc.__islocal) return;
    if (_DD_SKIP_DOCTYPES.includes(frm.doc.doctype)) return;
    _dd_check_and_add_button(frm);
});

function _dd_check_and_add_button(frm) {
    const dt = frm.doc.doctype;

    if (_dd_template_cache[dt] !== undefined) {
        if (_dd_template_cache[dt].length) {
            _dd_add_button(frm, _dd_template_cache[dt]);
        }
        return;
    }

    frappe.xcall("frappe.client.get_list", {
        doctype: "AK Document Template",
        filters: { reference_doctype: dt, is_active: 1 },
        fields: ["name", "template_name", "expires_in_days"],
        limit_page_length: 0,
    }).then((templates) => {
        _dd_template_cache[dt] = templates || [];
        if (_dd_template_cache[dt].length) {
            _dd_add_button(frm, _dd_template_cache[dt]);
        }
    }).catch(() => {
        _dd_template_cache[dt] = [];
    });
}

function _dd_add_button(frm, templates) {
    const label = __("Share via Doc Designer");
    if (frm.custom_buttons && frm.custom_buttons[label]) return;

    frm.add_custom_button(
        label,
        () => _dd_show_share_dialog(frm, templates),
        __("Create")
    );
}

function _dd_show_share_dialog(frm, templates) {
    const options = templates.map((t) => t.template_name);

    const d = new frappe.ui.Dialog({
        title: __("Share Document"),
        fields: [
            {
                fieldname: "template_display",
                fieldtype: "Select",
                label: __("Template"),
                options: options.join("\n"),
                default: options[0],
                reqd: 1,
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
                default: templates[0].expires_in_days || 7,
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
            // Map display name back to record name
            const selected = templates.find(
                (t) => t.template_name === values.template_display
            );
            if (!selected) return;

            d.hide();
            frappe.call({
                method: "doc_designer_ak.api.create_share",
                args: {
                    template: selected.name,
                    reference_doctype: frm.doc.doctype,
                    reference_name: frm.doc.name,
                    recipient_email: values.recipient_email || "",
                    expires_in_days: values.expires_in_days,
                },
                callback: (r) => {
                    if (!r.message) return;
                    const shareUrl = r.message.share_url;

                    if (values.send_email && values.recipient_email) {
                        frappe.call({
                            method: "doc_designer_ak.api.send_document_email",
                            args: { share_name: r.message.name },
                            callback: () => _dd_show_result(shareUrl, true),
                        });
                    } else {
                        _dd_show_result(shareUrl, false);
                    }
                },
            });
        },
    });

    // Update expiry when template changes
    d.fields_dict.template_display.$input.on("change", () => {
        const sel = templates.find(
            (t) => t.template_name === d.get_value("template_display")
        );
        if (sel) d.set_value("expires_in_days", sel.expires_in_days || 7);
    });

    d.show();
}

function _dd_show_result(url, emailSent) {
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
                frappe.show_alert({
                    message: __("Link copied!"),
                    indicator: "green",
                });
                d.hide();
            });
        },
    });

    d.show();

    d.$wrapper.find(".modal-footer").prepend(
        `<button class="btn btn-default btn-sm" onclick="window.open('${url}', '_blank')">${__("Preview")}</button>`
    );
}
