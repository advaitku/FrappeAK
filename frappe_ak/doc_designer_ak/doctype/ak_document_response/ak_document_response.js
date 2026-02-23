frappe.ui.form.on("AK Document Response", {
    refresh(frm) {
        if (frm.is_new()) return;

        frm.add_custom_button(__("View Filled Document"), () => {
            frappe.call({
                method: "frappe_ak.doc_api.render_response",
                args: { response_name: frm.doc.name },
                freeze: true,
                freeze_message: __("Rendering document..."),
                callback(r) {
                    if (!r.message) return;
                    _show_filled_document(r.message);
                },
            });
        }).addClass("btn-primary");

        // Link to original document
        if (frm.doc.reference_doctype && frm.doc.reference_name) {
            frm.add_custom_button(
                __(frm.doc.reference_name),
                () => frappe.set_route("Form", frm.doc.reference_doctype, frm.doc.reference_name),
                __("Go To")
            );
        }
    },
});

function _show_filled_document(data) {
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
