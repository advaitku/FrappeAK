frappe.ui.form.on("AK Automation Settings", {
	refresh(frm) {
		frm.add_custom_button(__("Test WhatsApp Connection"), function () {
			frappe.call({
				method: "frappe_ak.api.automation.test_whatsapp_connection",
				freeze: true,
				freeze_message: __("Testing connection..."),
				callback: function (r) {
					if (r.message && r.message.success) {
						frappe.msgprint(__("WhatsApp connection successful! Account: ") + r.message.account);
					} else {
						frappe.msgprint(__("Connection failed: ") + (r.message && r.message.error || "Unknown error"));
					}
				},
			});
		});
	},
});
