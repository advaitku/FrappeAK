(() => {
  // ../../../Documents/GitHub/FrappeAK/frappe_ak/public/js/share_button.bundle.js
  var _dd_template_cache = {};
  var _DD_SKIP_DOCTYPES = [
    "AK Document Template",
    "AK Document Share",
    "AK Document Response",
    "AK Document View Log",
    "AK Document Settings"
  ];
  $(document).on("form-refresh", function(e, frm) {
    if (!frm || !frm.doc || frm.doc.__islocal)
      return;
    if (_DD_SKIP_DOCTYPES.includes(frm.doc.doctype))
      return;
    _dd_check_and_add_button(frm);
  });
  function _dd_check_and_add_button(frm) {
    const dt = frm.doc.doctype;
    if (_dd_template_cache[dt] !== void 0) {
      if (_dd_template_cache[dt].length) {
        _dd_add_button(frm, _dd_template_cache[dt]);
      }
      return;
    }
    frappe.xcall("frappe.client.get_list", {
      doctype: "AK Document Template",
      filters: { reference_doctype: dt, is_active: 1 },
      fields: ["name", "template_name", "expires_in_days"],
      limit_page_length: 0
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
    if (frm.custom_buttons && frm.custom_buttons[label])
      return;
    frm.add_custom_button(
      label,
      () => _dd_show_share_dialog(frm, templates),
      __("Create")
    );
    const sharesLabel = __("Doc Designer Shares");
    if (frm.custom_buttons && frm.custom_buttons[sharesLabel])
      return;
    frm.add_custom_button(
      sharesLabel,
      () => _dd_show_shares_panel(frm),
      __("View")
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
          reqd: 1
        },
        {
          fieldname: "recipient_email",
          fieldtype: "Data",
          label: __("Recipient Email"),
          options: "Email"
        },
        {
          fieldname: "expires_in_days",
          fieldtype: "Int",
          label: __("Expires In (Days)"),
          default: templates[0].expires_in_days || 7,
          reqd: 1
        },
        {
          fieldname: "send_email",
          fieldtype: "Check",
          label: __("Send Email Now"),
          default: 0
        }
      ],
      primary_action_label: __("Create Share Link"),
      primary_action: (values) => {
        const selected = templates.find(
          (t) => t.template_name === values.template_display
        );
        if (!selected)
          return;
        d.hide();
        frappe.call({
          method: "frappe_ak.doc_api.create_share",
          args: {
            template: selected.name,
            reference_doctype: frm.doc.doctype,
            reference_name: frm.doc.name,
            recipient_email: values.recipient_email || "",
            expires_in_days: values.expires_in_days
          },
          callback: (r) => {
            if (!r.message)
              return;
            const shareUrl = r.message.share_url;
            if (values.send_email && values.recipient_email) {
              frappe.call({
                method: "frappe_ak.doc_api.send_document_email",
                args: { share_name: r.message.name },
                callback: () => _dd_show_result(shareUrl, true)
              });
            } else {
              _dd_show_result(shareUrl, false);
            }
          }
        });
      }
    });
    d.fields_dict.template_display.$input.on("change", () => {
      const sel = templates.find(
        (t) => t.template_name === d.get_value("template_display")
      );
      if (sel)
        d.set_value("expires_in_days", sel.expires_in_days || 7);
    });
    d.show();
  }
  function _dd_show_result(url, emailSent) {
    const msg = emailSent ? __("Share link created and email sent!") : __("Share link created!");
    const d = new frappe.ui.Dialog({
      title: msg,
      fields: [
        {
          fieldname: "share_url",
          fieldtype: "Data",
          label: __("Share URL"),
          default: url,
          read_only: 1
        }
      ],
      primary_action_label: __("Copy Link"),
      primary_action: () => {
        navigator.clipboard.writeText(url).then(() => {
          frappe.show_alert({
            message: __("Link copied!"),
            indicator: "green"
          });
          d.hide();
        });
      }
    });
    d.show();
    d.$wrapper.find(".modal-footer").prepend(
      `<button class="btn btn-default btn-sm" onclick="window.open('${url}', '_blank')">${__("Preview")}</button>`
    );
  }
  function _dd_show_shares_panel(frm) {
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "AK Document Share",
        filters: {
          reference_doctype: frm.doc.doctype,
          reference_name: frm.doc.name
        },
        fields: [
          "name",
          "template",
          "status",
          "recipient_email",
          "share_url",
          "creation",
          "submitted_at",
          "view_count"
        ],
        order_by: "creation desc",
        limit_page_length: 50
      },
      callback(r) {
        if (!r.message || !r.message.length) {
          frappe.msgprint(__("No Doc Designer shares found for this document."));
          return;
        }
        _dd_render_shares_dialog(frm, r.message);
      }
    });
  }
  function _dd_render_shares_dialog(frm, shares) {
    const d = new frappe.ui.Dialog({
      title: __("Doc Designer Shares \u2014 {0}", [frm.doc.name]),
      size: "extra-large"
    });
    const statusColors = {
      Active: { bg: "#eff6ff", border: "#93c5fd", text: "#2563eb" },
      Viewed: { bg: "#f5f3ff", border: "#c4b5fd", text: "#7c3aed" },
      Submitted: { bg: "#eff6ff", border: "#93c5fd", text: "#2563eb" },
      Accepted: { bg: "#f0fdf4", border: "#86efac", text: "#16a34a" },
      Declined: { bg: "#fef2f2", border: "#fca5a5", text: "#dc2626" },
      Expired: { bg: "#f9fafb", border: "#d1d5db", text: "#6b7280" }
    };
    let rows = "";
    for (const s of shares) {
      const sc = statusColors[s.status] || statusColors.Active;
      const badge = '<span style="display:inline-block;padding:2px 10px;border-radius:5px;font-size:12px;font-weight:600;border:1px solid ' + sc.border + ";background:" + sc.bg + ";color:" + sc.text + ';">' + frappe.utils.escape_html(s.status) + "</span>";
      const date = frappe.datetime.str_to_user(s.submitted_at || s.creation);
      const email = s.recipient_email ? frappe.utils.escape_html(s.recipient_email) : '<span style="color:#9ca3af;">\u2014</span>';
      let actions = '<div style="display:flex;gap:6px;justify-content:flex-end;">';
      if (["Submitted", "Accepted", "Declined"].includes(s.status)) {
        actions += '<button class="btn btn-xs btn-primary _dd-view-response" data-share="' + s.name + '">' + __("View Document") + "</button>";
      }
      actions += '<button class="btn btn-xs btn-default _dd-open-share" data-share="' + s.name + '">' + __("Details") + "</button>";
      actions += "</div>";
      rows += '<tr style="border-bottom:1px solid #f3f4f6;"><td style="padding:10px 12px;">' + badge + '</td><td style="padding:10px 12px;font-size:13px;">' + email + '</td><td style="padding:10px 12px;font-size:13px;color:#6b7280;">' + date + '</td><td style="padding:10px 12px;text-align:center;font-size:13px;">' + (s.view_count || 0) + '</td><td style="padding:10px 12px;">' + actions + "</td></tr>";
    }
    const html = '<div style="font-family:var(--font-stack);overflow:auto;"><table style="width:100%;border-collapse:collapse;"><thead><tr style="background:#f9fafb;border-bottom:2px solid #e5e7eb;"><th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;font-weight:600;">' + __("Status") + '</th><th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;font-weight:600;">' + __("Recipient") + '</th><th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:#6b7280;font-weight:600;">' + __("Date") + '</th><th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;color:#6b7280;font-weight:600;">' + __("Views") + '</th><th style="padding:8px 12px;text-align:right;font-size:11px;text-transform:uppercase;color:#6b7280;font-weight:600;">' + __("Actions") + "</th></tr></thead><tbody>" + rows + "</tbody></table></div>";
    d.$body.css({ padding: "0", overflow: "auto", "max-height": "70vh" });
    d.$body.html(html);
    d.$body.on("click", "._dd-view-response", function() {
      const shareName = $(this).data("share");
      d.hide();
      frappe.call({
        method: "frappe.client.get_list",
        args: {
          doctype: "AK Document Response",
          filters: { document_share: shareName },
          fields: ["name"],
          limit_page_length: 1,
          order_by: "creation desc"
        },
        callback(r) {
          if (r.message && r.message.length) {
            frappe.call({
              method: "frappe_ak.doc_api.render_response",
              args: { response_name: r.message[0].name },
              freeze: true,
              freeze_message: __("Rendering document..."),
              callback(r2) {
                if (r2.message) {
                  _dd_show_filled_inline(r2.message);
                }
              }
            });
          } else {
            frappe.msgprint(__("No response found for this share."));
          }
        }
      });
    });
    d.$body.on("click", "._dd-open-share", function() {
      const shareName = $(this).data("share");
      d.hide();
      frappe.set_route("Form", "AK Document Share", shareName);
    });
    d.show();
  }
  function _dd_show_filled_inline(data) {
    const d = new frappe.ui.Dialog({
      title: __("Filled Document"),
      size: "extra-large"
    });
    const badgeColors = {
      Accepted: { bg: "#f0fdf4", border: "#86efac", text: "#16a34a" },
      Declined: { bg: "#fef2f2", border: "#fca5a5", text: "#dc2626" },
      Submitted: { bg: "#eff6ff", border: "#93c5fd", text: "#2563eb" }
    };
    const bc = badgeColors[data.response_type] || badgeColors.Submitted;
    const submittedAt = data.submitted_at ? frappe.datetime.str_to_user(data.submitted_at) : "";
    let headerHtml = '<div style="display:flex;align-items:center;justify-content:space-between;padding:12px 20px;background:#f9fafb;border-bottom:1px solid #e5e7eb;font-size:13px;color:#6b7280;"><span style="display:inline-flex;align-items:center;gap:8px;"><span style="display:inline-block;padding:4px 12px;border-radius:6px;font-weight:600;font-size:12px;border:1px solid ' + bc.border + ";background:" + bc.bg + ";color:" + bc.text + ';">' + frappe.utils.escape_html(data.response_type) + "</span>";
    if (data.reference_name) {
      headerHtml += " &mdash; " + frappe.utils.escape_html(data.reference_name);
    }
    headerHtml += "</span>";
    if (submittedAt) {
      headerHtml += '<span style="font-size:12px;">' + __("Submitted") + " " + submittedAt + "</span>";
    }
    headerHtml += "</div>";
    d.$body.css({ padding: 0, overflow: "auto", "max-height": "75vh" });
    d.$body.html(
      headerHtml + "<style>" + (data.css || "") + '.ak-action-bar { display:none !important; }</style><div style="background:#fff;padding:40px;">' + (data.html || "") + "</div>"
    );
    d.show();
  }
})();
//# sourceMappingURL=share_button.bundle.SZMTQXHD.js.map
