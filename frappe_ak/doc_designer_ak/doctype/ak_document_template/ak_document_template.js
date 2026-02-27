frappe.ui.form.on("AK Document Template", {
    refresh(frm) {
        if (!frm.is_new()) {
            // Preview button
            frm.add_custom_button(__("Preview"), () => frm.trigger("render_preview"), __("Actions"));

            // Field Explorer button
            frm.add_custom_button(__("Field Explorer"), () => frm.trigger("show_field_explorer"), __("Actions"));

            // Helper Reference button
            frm.add_custom_button(__("Helper Reference"), () => frm.trigger("show_helper_reference"), __("Actions"));

            // Copy for AI button
            frm.add_custom_button(__("Copy for AI"), () => frm.trigger("copy_for_ai"), __("Actions"));

            // Duplicate Template button
            frm.add_custom_button(__("Duplicate"), () => {
                frappe.prompt(
                    { fieldname: "new_name", fieldtype: "Data", label: __("New Template Name"), reqd: 1 },
                    (values) => {
                        frappe.call({
                            method: "frappe.client.get",
                            args: { doctype: "AK Document Template", name: frm.doc.name },
                            callback(r) {
                                if (!r.message) return;
                                const copy = r.message;
                                delete copy.name;
                                copy.template_name = values.new_name;
                                copy.docstatus = 0;
                                frappe.call({
                                    method: "frappe.client.insert",
                                    args: { doc: copy },
                                    callback(r2) {
                                        if (r2.message) {
                                            frappe.set_route("Form", "AK Document Template", r2.message.name);
                                            frappe.show_alert({ message: __("Template duplicated!"), indicator: "green" });
                                        }
                                    },
                                });
                            },
                        });
                    },
                    __("Duplicate Template"),
                    __("Create Copy")
                );
            }, __("Actions"));
        }

        // Populate response action and display condition field options
        if (frm.doc.reference_doctype) {
            _ak_populate_response_action_fields(frm);
            _ak_populate_display_condition_fields(frm);
        }

        // Render preview if document is selected
        if (frm.doc.preview_document && frm.doc.reference_doctype) {
            frm.trigger("render_preview");
        } else {
            frm.fields_dict.preview_html && frm.fields_dict.preview_html.$wrapper.html(
                '<div style="padding:24px;text-align:center;color:#9ca3af;">' +
                'Select a <strong>Preview Document</strong> above to see a live preview of your template.' +
                '</div>'
            );
        }
    },

    preview_document(frm) {
        if (frm.doc.preview_document) {
            frm.trigger("render_preview");
        }
    },

    reference_doctype(frm) {
        frm.set_value("preview_document", "");
        frm.set_value("auto_send_doctype_filter", "");
        if (frm.doc.reference_doctype) {
            _ak_populate_response_action_fields(frm);
            _ak_populate_display_condition_fields(frm);
        }
    },

    render_preview(frm) {
        if (!frm.doc.template_name) {
            frappe.msgprint(__("Please save the template first."));
            return;
        }

        // Save first to ensure latest HTML is used
        if (frm.dirty()) {
            frm.save().then(() => frm.trigger("_do_preview"));
        } else {
            frm.trigger("_do_preview");
        }
    },

    _do_preview(frm) {
        const $wrapper = frm.fields_dict.preview_html.$wrapper;
        $wrapper.html('<div style="padding:24px;text-align:center;color:#6b7280;">Rendering preview...</div>');

        frappe.call({
            method: "frappe_ak.doc_api.preview_template",
            args: {
                template_name: frm.doc.template_name,
                reference_name: frm.doc.preview_document || "",
            },
            callback(r) {
                if (r.message) {
                    const css = r.message.css || "";
                    const html = r.message.html || "";
                    $wrapper.html(
                        '<div class="ak-preview-container">' +
                        '<style>' +
                        '.ak-preview-container { border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; background: #f9fafb; }' +
                        '.ak-preview-header { display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; background: #f3f4f6; border-bottom: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }' +
                        '.ak-preview-frame { background: #fff; padding: 40px; max-height: 600px; overflow-y: auto; }' +
                        css +
                        '</style>' +
                        '<div class="ak-preview-header">' +
                        '<span>Preview' + (frm.doc.preview_document ? ' — ' + frm.doc.preview_document : ' — No document selected') + '</span>' +
                        '<button class="btn btn-xs btn-default ak-preview-fullscreen-btn">Open Full Preview</button>' +
                        '</div>' +
                        '<div class="ak-preview-frame">' + html + '</div>' +
                        '</div>'
                    );

                    // Full preview in new dialog
                    $wrapper.find(".ak-preview-fullscreen-btn").on("click", function () {
                        let d = new frappe.ui.Dialog({
                            title: __("Template Preview"),
                            size: "extra-large",
                        });
                        d.$body.css({ padding: 0, overflow: "auto" });
                        d.$body.html(
                            '<style>' + css + '</style>' +
                            '<div style="background:#fff;padding:40px;">' + html + '</div>'
                        );
                        d.show();
                    });
                }
            },
            error() {
                $wrapper.html(
                    '<div style="padding:16px;color:#dc2626;">Failed to render preview. Check your template for errors.</div>'
                );
            },
        });
    },

    show_field_explorer(frm) {
        if (!frm.doc.reference_doctype) {
            frappe.msgprint(__("Please select a Reference DocType first."));
            return;
        }

        frappe.call({
            method: "frappe_ak.doc_api.get_doctype_fields",
            args: { doctype_name: frm.doc.reference_doctype },
            callback(r) {
                if (!r.message) return;

                const { fields, child_tables } = r.message;
                let html = build_field_explorer_html(fields, child_tables, frm.doc.reference_doctype);

                let d = new frappe.ui.Dialog({
                    title: __("Field Explorer — {0}", [frm.doc.reference_doctype]),
                    size: "extra-large",
                });

                d.$body.css({ padding: "16px", "max-height": "70vh", overflow: "auto" });
                d.$body.html(html);

                // Copy on click
                d.$body.on("click", ".ak-fe-copy", function () {
                    const text = $(this).data("copy");
                    navigator.clipboard.writeText(text).then(() => {
                        frappe.show_alert({ message: __("Copied: {0}", [text]), indicator: "green" }, 2);
                    });
                });

                // Search/filter
                d.$body.on("input", ".ak-fe-search", function () {
                    const q = $(this).val().toLowerCase();
                    d.$body.find(".ak-fe-row").each(function () {
                        const match = $(this).text().toLowerCase().includes(q);
                        $(this).toggle(match);
                    });
                });

                // Tab switching
                d.$body.on("click", ".ak-fe-tab", function () {
                    const tab = $(this).data("tab");
                    d.$body.find(".ak-fe-tab").removeClass("btn-primary").addClass("btn-default");
                    $(this).removeClass("btn-default").addClass("btn-primary");
                    d.$body.find(".ak-fe-panel").hide();
                    d.$body.find('.ak-fe-panel[data-panel="' + tab + '"]').show();
                });

                d.show();
            },
        });
    },

    show_helper_reference(frm) {
        const helpers = [
            {
                name: "ak_input",
                desc: "Text input field",
                signature: 'ak_input("field_name", label="Label", value="", placeholder="", editable=True, mandatory=False, input_type="text")',
                example: '{{ ak_input("customer_po", label="PO Number", mandatory=True) }}',
            },
            {
                name: "ak_textarea",
                desc: "Multi-line text area",
                signature: 'ak_textarea("field_name", label="Label", value="", rows=4, editable=True, mandatory=False)',
                example: '{{ ak_textarea("comments", label="Comments", rows=3) }}',
            },
            {
                name: "ak_date",
                desc: "Date picker",
                signature: 'ak_date("field_name", label="Label", value="", editable=True, mandatory=False)',
                example: '{{ ak_date("delivery_date", label="Delivery Date", value=doc.delivery_date, mandatory=True) }}',
            },
            {
                name: "ak_datetime",
                desc: "Date + time picker",
                signature: 'ak_datetime("field_name", label="Label", value="", editable=True, mandatory=False)',
                example: '{{ ak_datetime("meeting_time", label="Meeting Time") }}',
            },
            {
                name: "ak_checkbox",
                desc: "Checkbox toggle",
                signature: 'ak_checkbox("field_name", label="Label", checked=False, editable=True)',
                example: '{{ ak_checkbox("agree_terms", label="I agree to the terms") }}',
            },
            {
                name: "ak_select",
                desc: "Dropdown select",
                signature: 'ak_select("field_name", label="Label", options=[], value="", editable=True, mandatory=False)',
                example: '{{ ak_select("priority", label="Priority", options=["Low", "Medium", "High"], value="Medium") }}',
            },
            {
                name: "ak_field_table",
                desc: "Auto-render all fields from the Interactive Fields table",
                signature: 'ak_field_table(columns=1)',
                example: '{{ ak_field_table(columns=2) }}',
            },
            {
                name: "ak_items_table",
                desc: "Pricing/items table from doc.items",
                signature: 'ak_items_table(doc, columns=["item_name","qty","rate","amount"], show_total=True)',
                example: '{{ ak_items_table(doc) }}',
            },
            {
                name: "ak_accept_decline",
                desc: "Accept/Decline buttons for approvals",
                signature: 'ak_accept_decline(accept_label="Accept", decline_label="Decline")',
                example: '{{ ak_accept_decline(accept_label="Approve", decline_label="Reject") }}',
            },
            {
                name: "ak_submit_button",
                desc: "Submit button for forms",
                signature: 'ak_submit_button(label="Submit")',
                example: '{{ ak_submit_button(label="Submit Feedback") }}',
            },
        ];

        const conditionals = [
            {
                name: "Simple if",
                code: '{% if doc.status == "Overdue" %}\n  <div class="ak-notice">Payment is overdue!</div>\n{% endif %}',
            },
            {
                name: "If / else",
                code: '{% if doc.grand_total > 10000 %}\n  {{ ak_input("po_number", label="PO Number", mandatory=True) }}\n{% else %}\n  <p>No PO required for orders under $10,000.</p>\n{% endif %}',
            },
            {
                name: "Multiple conditions",
                code: '{% if doc.status == "Draft" %}\n  <div class="ak-notice">This is a draft.</div>\n{% elif doc.status == "Overdue" %}\n  <div class="ak-notice" style="background:#fef2f2;border-color:#ef4444;color:#dc2626;">Overdue!</div>\n{% else %}\n  <p>Status: {{ doc.status }}</p>\n{% endif %}',
            },
            {
                name: "Loop child table",
                code: '{% for item in doc.items %}\n  <p>{{ item.item_name }} — Qty: {{ item.qty }}</p>\n{% endfor %}',
            },
            {
                name: "Check if field exists",
                code: '{% if doc.po_no %}\n  <p>PO: {{ doc.po_no }}</p>\n{% endif %}',
            },
            {
                name: "Count items",
                code: '{% if doc.items | length > 5 %}\n  <div class="ak-notice">This order has {{ doc.items | length }} items.</div>\n{% endif %}',
            },
        ];

        let html = '<div style="font-family:var(--font-stack);font-size:13px;">';

        // Tabs
        html += '<div style="margin-bottom:12px;display:flex;gap:8px;">';
        html += '<button class="btn btn-sm btn-primary ak-hr-tab" data-tab="helpers">Helper Functions</button>';
        html += '<button class="btn btn-sm btn-default ak-hr-tab" data-tab="conditions">Conditional Logic</button>';
        html += '<button class="btn btn-sm btn-default ak-hr-tab" data-tab="utilities">Utilities</button>';
        html += '</div>';

        // Helper Functions panel
        html += '<div class="ak-hr-panel" data-panel="helpers">';
        for (const h of helpers) {
            html += '<div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px;">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">';
            html += '<strong style="color:#4f46e5;">' + h.name + '</strong>';
            html += '<span style="color:#6b7280;font-size:12px;">' + h.desc + '</span>';
            html += '</div>';
            html += '<div style="background:#f9fafb;padding:8px;border-radius:4px;font-family:monospace;font-size:12px;margin-bottom:4px;word-break:break-all;">' + frappe.utils.escape_html(h.signature) + '</div>';
            html += '<div style="display:flex;align-items:center;gap:8px;">';
            html += '<code style="flex:1;background:#f0fdf4;padding:6px 8px;border-radius:4px;font-size:12px;display:block;overflow-x:auto;">' + frappe.utils.escape_html(h.example) + '</code>';
            html += '<button class="btn btn-xs btn-default ak-hr-copy" data-copy="' + frappe.utils.escape_html(h.example) + '">Copy</button>';
            html += '</div></div>';
        }
        html += '</div>';

        // Conditionals panel
        html += '<div class="ak-hr-panel" data-panel="conditions" style="display:none;">';
        for (const c of conditionals) {
            html += '<div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px;margin-bottom:8px;">';
            html += '<strong style="margin-bottom:4px;display:block;">' + c.name + '</strong>';
            html += '<pre style="background:#f9fafb;padding:10px;border-radius:4px;font-size:12px;margin:0;overflow-x:auto;white-space:pre-wrap;">' + frappe.utils.escape_html(c.code) + '</pre>';
            html += '<button class="btn btn-xs btn-default ak-hr-copy" style="margin-top:6px;" data-copy="' + frappe.utils.escape_html(c.code) + '">Copy</button>';
            html += '</div>';
        }
        html += '</div>';

        // Utilities panel
        html += '<div class="ak-hr-panel" data-panel="utilities" style="display:none;">';
        const utils = [
            { code: '{{ doc.field_name }}', desc: 'Output any document field' },
            { code: '{{ doc.field_name or "N/A" }}', desc: 'Default value if empty' },
            { code: '{{ format_currency(doc.grand_total) }}', desc: 'Format as currency' },
            { code: '{{ frappe.utils.formatdate(doc.posting_date) }}', desc: 'Format date' },
            { code: '{{ frappe.utils.fmt_money(doc.amount, currency="USD") }}', desc: 'Format money with currency' },
            { code: '{{ nowdate() }}', desc: "Today's date" },
            { code: '{{ doc.items | length }}', desc: 'Count child table rows' },
            { code: '{{ doc.description | truncate(100) }}', desc: 'Truncate text' },
            { code: '<div class="ak-page-break"></div>', desc: 'Page break for PDF' },
            { code: '<div class="ak-notice">Warning text</div>', desc: 'Notice/warning box' },
        ];
        for (const u of utils) {
            html += '<div class="ak-fe-row" style="display:flex;align-items:center;gap:8px;padding:8px;border-bottom:1px solid #f3f4f6;">';
            html += '<code style="flex:1;font-size:12px;background:#f9fafb;padding:4px 8px;border-radius:4px;">' + frappe.utils.escape_html(u.code) + '</code>';
            html += '<span style="color:#6b7280;font-size:12px;min-width:200px;">' + u.desc + '</span>';
            html += '<button class="btn btn-xs btn-default ak-hr-copy" data-copy="' + frappe.utils.escape_html(u.code) + '">Copy</button>';
            html += '</div>';
        }
        html += '</div>';

        html += '</div>';

        let d = new frappe.ui.Dialog({
            title: __("Helper Reference"),
            size: "extra-large",
        });
        d.$body.css({ padding: "16px", "max-height": "70vh", overflow: "auto" });
        d.$body.html(html);

        // Copy
        d.$body.on("click", ".ak-hr-copy", function () {
            const text = $(this).data("copy");
            navigator.clipboard.writeText(text).then(() => {
                frappe.show_alert({ message: __("Copied!"), indicator: "green" }, 2);
            });
        });

        // Tab switching
        d.$body.on("click", ".ak-hr-tab", function () {
            const tab = $(this).data("tab");
            d.$body.find(".ak-hr-tab").removeClass("btn-primary").addClass("btn-default");
            $(this).removeClass("btn-default").addClass("btn-primary");
            d.$body.find(".ak-hr-panel").hide();
            d.$body.find('.ak-hr-panel[data-panel="' + tab + '"]').show();
        });

        d.show();
    },

    copy_for_ai(frm) {
        if (!frm.doc.reference_doctype) {
            frappe.msgprint(__("Please select a Reference DocType first."));
            return;
        }

        frappe.call({
            method: "frappe_ak.doc_api.get_doctype_fields",
            args: { doctype_name: frm.doc.reference_doctype },
            callback(r) {
                if (!r.message) return;

                const { fields, child_tables } = r.message;
                let text = "";

                text += "# AK Document Template — Field & Helper Reference\n";
                text += "## DocType: " + frm.doc.reference_doctype + "\n\n";

                // Document Fields
                text += "## Document Fields\n";
                text += "| fieldname | label | type | merge tag |\n";
                text += "|-----------|-------|------|----------|\n";
                for (const f of fields) {
                    if (f.fieldtype === "Table" || f.fieldtype === "Table MultiSelect") continue;
                    text += "| " + f.fieldname + " | " + (f.label || "") + " | " + f.fieldtype
                        + " | {{ doc." + f.fieldname + " }} |\n";
                }
                text += "\n";

                // Child Tables
                const childKeys = Object.keys(child_tables);
                for (const key of childKeys) {
                    const ct = child_tables[key];
                    text += "## Child Table: " + key + " (" + ct.doctype + ")\n";
                    text += "Loop: {% for row in doc." + key + " %}...{% endfor %}\n";
                    text += "| fieldname | label | type | in loop |\n";
                    text += "|-----------|-------|------|--------|\n";
                    for (const cf of ct.fields) {
                        text += "| " + cf.fieldname + " | " + (cf.label || "") + " | " + cf.fieldtype
                            + " | {{ row." + cf.fieldname + " }} |\n";
                    }
                    text += "\n";
                }

                // Helper Functions
                text += "## Jinja2 Helper Functions\n";
                text += '- {{ ak_input("fieldname", label="Label", value=doc.fieldname, placeholder="", editable=True, mandatory=False, input_type="text") }} — Text/number/email input\n';
                text += '- {{ ak_textarea("fieldname", label="Label", value=doc.fieldname, rows=4, editable=True, mandatory=False) }} — Multi-line text\n';
                text += '- {{ ak_date("fieldname", label="Label", value=doc.fieldname, editable=True, mandatory=False) }} — Date picker\n';
                text += '- {{ ak_datetime("fieldname", label="Label", value=doc.fieldname, editable=True, mandatory=False) }} — Date+time picker\n';
                text += '- {{ ak_checkbox("fieldname", label="Label", checked=doc.fieldname, editable=True) }} — Checkbox\n';
                text += '- {{ ak_select("fieldname", label="Label", options=["A","B","C"], value=doc.fieldname, editable=True, mandatory=False) }} — Dropdown\n';
                text += '- {{ ak_field_table(columns=2) }} — Auto-renders all fields from the Interactive Fields table (1 or 2 columns)\n';
                text += '- {{ ak_items_table(doc, columns=["item_name","qty","rate","amount"], show_total=True) }} — Items/pricing table\n';
                text += '- {{ ak_accept_decline(accept_label="Accept", decline_label="Decline") }} — Accept/Decline action bar\n';
                text += '- {{ ak_submit_button(label="Submit") }} — Submit action bar\n\n';

                // Utilities
                text += "## Utilities & Conditionals\n";
                text += '- {{ doc.fieldname }} — Output any field value\n';
                text += '- {{ doc.fieldname or "N/A" }} — Default value if empty\n';
                text += '- {{ format_currency(doc.grand_total) }} — Format as currency\n';
                text += '- {{ frappe.utils.formatdate(doc.posting_date) }} — Format date\n';
                text += '- {{ frappe.utils.fmt_money(doc.amount, currency="USD") }} — Format money with currency\n';
                text += '- {{ nowdate() }} — Today\'s date\n';
                text += '- {{ doc.items | length }} — Count child table rows\n';
                text += '- {% if doc.fieldname %}...{% endif %} — Conditional block\n';
                text += '- {% if doc.status == "Draft" %}...{% elif doc.status == "Overdue" %}...{% else %}...{% endif %} — Multiple conditions\n';
                text += '- {% for row in doc.child_table %}{{ row.field }}{% endfor %} — Loop child table\n';
                text += '- <div class="ak-page-break"></div> — Page break for PDF\n';
                text += '- <div class="ak-notice">Warning text</div> — Notice/warning box\n';

                navigator.clipboard.writeText(text).then(() => {
                    frappe.show_alert({
                        message: __("Copied! Paste into your AI chat to generate template HTML."),
                        indicator: "green",
                    }, 5);
                });
            },
        });
    },
});


function build_field_explorer_html(fields, child_tables, doctype) {
    let html = '<div style="font-family:var(--font-stack);font-size:13px;">';

    // Search bar
    html += '<input class="ak-fe-search form-control input-sm" placeholder="Search fields..." style="margin-bottom:12px;" />';

    // Tabs
    const tabNames = ["Fields"];
    const childKeys = Object.keys(child_tables);
    for (const key of childKeys) {
        tabNames.push(child_tables[key].label || key);
    }

    html += '<div style="margin-bottom:12px;display:flex;gap:6px;flex-wrap:wrap;">';
    html += '<button class="btn btn-sm btn-primary ak-fe-tab" data-tab="fields">Document Fields</button>';
    for (const key of childKeys) {
        html += '<button class="btn btn-sm btn-default ak-fe-tab" data-tab="child_' + key + '">' + (child_tables[key].label || key) + '</button>';
    }
    html += '</div>';

    // Document fields panel
    html += '<div class="ak-fe-panel" data-panel="fields">';
    html += '<table style="width:100%;border-collapse:collapse;">';
    html += '<thead><tr style="background:#f3f4f6;"><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">Field</th><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">Label</th><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">Type</th><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">Merge Tag</th><th style="padding:6px 10px;"></th></tr></thead>';
    html += '<tbody>';
    for (const f of fields) {
        const tag = '{{ doc.' + f.fieldname + ' }}';
        const condTag = '{% if doc.' + f.fieldname + ' %}...{% endif %}';
        html += '<tr class="ak-fe-row" style="border-bottom:1px solid #f3f4f6;">';
        html += '<td style="padding:6px 10px;font-family:monospace;font-size:12px;color:#4f46e5;">' + f.fieldname + '</td>';
        html += '<td style="padding:6px 10px;">' + (f.label || '') + (f.reqd ? ' <span style="color:#ef4444;">*</span>' : '') + '</td>';
        html += '<td style="padding:6px 10px;font-size:12px;color:#6b7280;">' + f.fieldtype + '</td>';
        html += '<td style="padding:6px 10px;"><code style="font-size:11px;background:#f9fafb;padding:2px 6px;border-radius:3px;">' + frappe.utils.escape_html(tag) + '</code></td>';
        html += '<td style="padding:6px 10px;white-space:nowrap;">';
        html += '<button class="btn btn-xs btn-default ak-fe-copy" data-copy="' + frappe.utils.escape_html(tag) + '" title="Copy merge tag">Copy</button> ';
        html += '<button class="btn btn-xs btn-default ak-fe-copy" data-copy="' + frappe.utils.escape_html(condTag) + '" title="Copy conditional block">{% if %}</button>';
        html += '</td>';
        html += '</tr>';
    }
    html += '</tbody></table>';
    html += '</div>';

    // Child table panels
    for (const key of childKeys) {
        const ct = child_tables[key];
        html += '<div class="ak-fe-panel" data-panel="child_' + key + '" style="display:none;">';
        html += '<p style="margin-bottom:8px;color:#6b7280;">Loop: <code style="font-size:12px;background:#f0fdf4;padding:2px 6px;border-radius:3px;">{% for row in doc.' + key + ' %}...{% endfor %}</code> ';
        html += '<button class="btn btn-xs btn-default ak-fe-copy" data-copy="' + frappe.utils.escape_html('{% for row in doc.' + key + ' %}\n  {{ row.FIELD }}\n{% endfor %}') + '">Copy Loop</button></p>';
        html += '<table style="width:100%;border-collapse:collapse;">';
        html += '<thead><tr style="background:#f3f4f6;"><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">Field</th><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">Label</th><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">Type</th><th style="padding:6px 10px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;">In Loop</th><th style="padding:6px 10px;"></th></tr></thead>';
        html += '<tbody>';
        for (const cf of ct.fields) {
            const tag = '{{ row.' + cf.fieldname + ' }}';
            html += '<tr class="ak-fe-row" style="border-bottom:1px solid #f3f4f6;">';
            html += '<td style="padding:6px 10px;font-family:monospace;font-size:12px;color:#4f46e5;">' + cf.fieldname + '</td>';
            html += '<td style="padding:6px 10px;">' + (cf.label || '') + '</td>';
            html += '<td style="padding:6px 10px;font-size:12px;color:#6b7280;">' + cf.fieldtype + '</td>';
            html += '<td style="padding:6px 10px;"><code style="font-size:11px;background:#f9fafb;padding:2px 6px;border-radius:3px;">' + frappe.utils.escape_html(tag) + '</code></td>';
            html += '<td style="padding:6px 10px;"><button class="btn btn-xs btn-default ak-fe-copy" data-copy="' + frappe.utils.escape_html(tag) + '">Copy</button></td>';
            html += '</tr>';
        }
        html += '</tbody></table>';
        html += '</div>';
    }

    html += '</div>';
    return html;
}


// ── Response Action child table: populate field_name and value options ──

// Cache: { "Sales Order": { fields_str: "\nstatus\n...", meta: { status: {fieldtype, options}, ... } } }
let _ak_ra_cache = {};

function _ak_populate_response_action_fields(frm) {
    const ref_dt = frm.doc.reference_doctype;
    if (!ref_dt) return;

    const apply = (cache) => {
        const grid = frm.fields_dict.response_actions.grid;
        grid.update_docfield_property("field_name", "options", cache.fields_str);
        grid.refresh();
    };

    if (_ak_ra_cache[ref_dt]) {
        apply(_ak_ra_cache[ref_dt]);
        return;
    }

    frappe.call({
        method: "frappe_ak.doc_api.get_doctype_fields",
        args: { doctype_name: ref_dt },
        callback(r) {
            if (r.message && r.message.fields) {
                const meta = {};
                const names = [];
                for (const f of r.message.fields) {
                    if (["Table", "Table MultiSelect"].includes(f.fieldtype)) continue;
                    names.push(f.fieldname);
                    meta[f.fieldname] = {
                        fieldtype: f.fieldtype,
                        options: f.options || "",
                        label: f.label || f.fieldname,
                    };
                }
                _ak_ra_cache[ref_dt] = {
                    fields_str: "\n" + names.join("\n"),
                    meta: meta,
                };
                apply(_ak_ra_cache[ref_dt]);
            }
        },
    });
}

function _ak_get_value_options_for_field(frm, fieldname) {
    const ref_dt = frm.doc.reference_doctype;
    const cache = _ak_ra_cache[ref_dt];
    if (!cache || !cache.meta[fieldname]) return null;

    const fm = cache.meta[fieldname];

    // Select fields — return newline-separated options
    if (fm.fieldtype === "Select" && fm.options) {
        return fm.options;
    }

    // Check field — return 0/1
    if (fm.fieldtype === "Check") {
        return "0\n1";
    }

    return null;
}

frappe.ui.form.on("AK Response Action", {
    field_name(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.field_name) return;

        const options = _ak_get_value_options_for_field(frm, row.field_name);
        const grid = frm.fields_dict.response_actions.grid;
        const grid_row = grid.grid_rows_by_docname[cdn];
        if (!grid_row) return;

        if (options) {
            // Temporarily change value column to Select for this interaction
            grid.update_docfield_property("value", "fieldtype", "Select");
            grid.update_docfield_property("value", "options", "\n" + options);
            grid.refresh();
        } else {
            // Revert to Data for free-text entry
            grid.update_docfield_property("value", "fieldtype", "Data");
            grid.update_docfield_property("value", "options", "");
            grid.refresh();
        }
    },
});


// ── Display Condition child table: populate field_name options ──

function _ak_populate_display_condition_fields(frm) {
    const ref_dt = frm.doc.reference_doctype;
    if (!ref_dt) return;

    const apply = (cache) => {
        const grid = frm.fields_dict.display_conditions.grid;
        grid.update_docfield_property("field_name", "options", cache.fields_str);
        grid.refresh();
    };

    // Reuse the same cache as response action fields
    if (_ak_ra_cache[ref_dt]) {
        apply(_ak_ra_cache[ref_dt]);
        return;
    }

    frappe.call({
        method: "frappe_ak.doc_api.get_doctype_fields",
        args: { doctype_name: ref_dt },
        callback(r) {
            if (r.message && r.message.fields) {
                const meta = {};
                const names = [];
                for (const f of r.message.fields) {
                    if (["Table", "Table MultiSelect"].includes(f.fieldtype)) continue;
                    names.push(f.fieldname);
                    meta[f.fieldname] = {
                        fieldtype: f.fieldtype,
                        options: f.options || "",
                        label: f.label || f.fieldname,
                    };
                }
                _ak_ra_cache[ref_dt] = {
                    fields_str: "\n" + names.join("\n"),
                    meta: meta,
                };
                apply(_ak_ra_cache[ref_dt]);
            }
        },
    });
}

frappe.ui.form.on("AK Display Condition", {
    field_name(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (!row.field_name) return;

        const options = _ak_get_value_options_for_field(frm, row.field_name);
        const grid = frm.fields_dict.display_conditions.grid;

        if (options) {
            grid.update_docfield_property("value", "fieldtype", "Select");
            grid.update_docfield_property("value", "options", "\n" + options);
        } else {
            grid.update_docfield_property("value", "fieldtype", "Data");
            grid.update_docfield_property("value", "options", "");
        }
        grid.refresh();
    },

    operator(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const grid = frm.fields_dict.display_conditions.grid;

        if (row.operator === "is set" || row.operator === "is not set") {
            frappe.model.set_value(cdt, cdn, "value", "");
            grid.update_docfield_property("value", "read_only", 1);
        } else {
            grid.update_docfield_property("value", "read_only", 0);
        }
        grid.refresh();
    },
});
