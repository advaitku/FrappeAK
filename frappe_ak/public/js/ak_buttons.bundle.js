// AutomationAK — Button/Macro injection script
// Loaded globally via app_include_js. Adds automation buttons to DocType forms.

let _ak_automation_cache = {};

// Skip our own doctypes
const _AK_SKIP_DOCTYPES = ["AK Automation", "AK Automation Log", "AK Automation Settings"];

// Hook into every form's refresh event using Frappe's standard form_events system.
// This is more reliable than $(document).on("form-refresh") which can miss events
// or fire at the wrong time in the rendering cycle.
if (frappe.ui && frappe.ui.form) {
	const _origMake = frappe.ui.form.Form.prototype.refresh;
	frappe.ui.form.Form.prototype.refresh = function (...args) {
		const ret = _origMake.apply(this, args);

		const frm = this;
		if (!frm || !frm.doc || frm.doc.__islocal) return ret;

		const dt = frm.doc.doctype;
		if (_AK_SKIP_DOCTYPES.includes(dt)) return ret;

		_ak_load_and_add_buttons(frm, dt);

		return ret;
	};
}

// Fallback: also listen on the jQuery event for edge cases (e.g. if the
// prototype override ran before frappe.ui.form was fully initialised).
$(document).on("form-refresh", function (e, frm) {
	if (!frm || !frm.doc || frm.doc.__islocal) return;
	let dt = frm.doc.doctype;
	if (_AK_SKIP_DOCTYPES.includes(dt)) return;
	_ak_load_and_add_buttons(frm, dt);
});

function _ak_load_and_add_buttons(frm, dt) {
	// Use cache if available
	if (_ak_automation_cache[dt] !== undefined) {
		_ak_add_buttons(frm, _ak_automation_cache[dt]);
		return;
	}

	frappe.xcall("frappe_ak.api.automation.get_button_automations", { doctype: dt })
		.then(function (automations) {
			_ak_automation_cache[dt] = automations || [];
			_ak_add_buttons(frm, _ak_automation_cache[dt]);
		})
		.catch(function (err) {
			console.warn("AutomationAK: could not load button automations for", dt, err);
			_ak_automation_cache[dt] = [];
		});
}

function _ak_add_buttons(frm, automations) {
	if (!automations || !automations.length) return;

	automations.forEach(function (auto) {
		// Avoid duplicate buttons on repeated refreshes
		let label = __(auto.button_label || auto.title);
		let group = __("Automations");
		if (frm.custom_buttons && frm.custom_buttons[label]) return;

		frm.add_custom_button(
			label,
			function () {
				frappe.call({
					method: "frappe_ak.api.automation.run_button_automation",
					args: {
						automation_name: auto.name,
						doctype: frm.doc.doctype,
						docname: frm.doc.name,
					},
					freeze: true,
					freeze_message: __("Running automation..."),
					callback: function (r) {
						if (r.message) {
							let indicator = r.message.status === "ok" ? "green" : "orange";
							frappe.show_alert({
								message: r.message.message,
								indicator: indicator,
							});
							frm.reload_doc();
						}
					},
				});
			},
			group
		);
	});
}
