frappe.listview_settings["AK Automation Log"] = {
	get_indicator(doc) {
		const status_map = {
			Success: [__("Success"), "green", "status,=,Success"],
			Failed: [__("Failed"), "red", "status,=,Failed"],
			Skipped: [__("Skipped"), "orange", "status,=,Skipped"],
		};
		return status_map[doc.status] || [__("Unknown"), "grey", ""];
	},
};
