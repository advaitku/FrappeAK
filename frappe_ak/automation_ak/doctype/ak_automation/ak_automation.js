frappe.ui.form.on("AK Automation", {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Test Automation"), function () {
				frappe.call({
					method: "frappe_ak.api.automation.test_automation",
					args: { automation_name: frm.doc.name },
					freeze: true,
					freeze_message: __("Testing..."),
					callback: function (r) {
						if (r.message) {
							frappe.msgprint({
								title: __("Test Result"),
								message: `<strong>Document:</strong> ${r.message.document}<br>
									<strong>Conditions Met:</strong> ${r.message.conditions_met ? "Yes" : "No"}<br>
									<strong>Actions:</strong> ${r.message.actions_count}<br><br>
									${r.message.message}`,
								indicator: r.message.conditions_met ? "green" : "orange",
							});
						}
					},
				});
			});
		}

		if (frm.doc.reference_doctype) {
			_load_doctype_fields(frm);
		}

		// Hide the raw field_updates child table — managed inline in action rows
		frm.set_df_property("sb_field_updates", "hidden", 1);
	},

	reference_doctype(frm) {
		if (frm.doc.reference_doctype) {
			_load_doctype_fields(frm);
		}
	},

	trigger_type(frm) {
		frm.refresh_fields();
	},
});

// ── Condition events ──
frappe.ui.form.on("AK Automation Condition", {
	field(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.field && frm.doc.reference_doctype) {
			frappe.call({
				method: "frappe_ak.api.automation.get_operators_for_field",
				args: { doctype: frm.doc.reference_doctype, fieldname: row.field },
				callback: function (r) {
					if (r.message) {
						row.__operators = r.message;
						_set_child_field_options(frm, cdt, cdn, "operator", r.message);
					}
				},
			});
		}
	},
});

// ── Action events ──
frappe.ui.form.on("AK Automation Action", {
	action_type(frm, cdt, cdn) {
		frm.refresh_fields();
		let row = locals[cdt][cdn];
		if (["Update Fields", "Field Formulas"].includes(row.action_type)) {
			setTimeout(() => _render_field_updates_html(frm, cdt, cdn), 150);
		}
	},

	form_render(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (["Update Fields", "Field Formulas"].includes(row.action_type)) {
			// Small delay to ensure the grid form is fully rendered
			setTimeout(() => _render_field_updates_html(frm, cdt, cdn), 50);
		}
	},
});

// ── Field Update events (fallback for direct child table editing) ──
frappe.ui.form.on("AK Field Update", {});

// ══════════════════════════════════════════════════════════
//  Render field updates table inside expanded action row
// ══════════════════════════════════════════════════════════

function _render_field_updates_html(frm, cdt, cdn) {
	let action_row = locals[cdt][cdn];
	let grid_row = frm.fields_dict.actions.grid.grid_rows_by_docname[cdn];
	if (!grid_row || !grid_row.grid_form) return;

	let html_field = grid_row.grid_form.fields_dict.field_updates_html;
	if (!html_field) return;

	let $w = $(html_field.wrapper).empty();
	let action_idx = action_row.idx;
	let updates = (frm.doc.field_updates || []).filter(
		(u) => u.parent_action_idx === action_idx
	);

	let $c = $('<div class="ak-field-updates-inline" style="margin-top:4px;"></div>');

	if (updates.length) {
		updates.forEach(function (u, i) {
			let label = u.target_field;
			let meta = (frm.__doctype_fields || []).find((f) => f.fieldname === u.target_field);
			if (meta) label = meta.label;

			let summary = u.display_summary || u.value || "";

			let $row = $(`
				<div style="display:flex; align-items:center; gap:8px; padding:6px 8px; border:1px solid var(--border-color); border-radius:6px; margin-bottom:6px; background:var(--fg-color);">
					<div style="flex:1; min-width:0;">
						<span style="font-weight:600; font-size:13px;">${frappe.utils.escape_html(label)}</span>
						<span style="color:var(--text-muted); font-size:12px; margin-left:6px;">${frappe.utils.escape_html(u.value_type || "")}</span>
						<div style="font-size:12px; color:var(--text-light); margin-top:2px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
							<code style="font-size:12px;">${frappe.utils.escape_html(summary)}</code>
						</div>
					</div>
					<button class="btn btn-xs btn-default ak-edit-fu" title="${__("Edit")}">
						<svg class="icon icon-sm"><use href="#icon-edit"></use></svg>
					</button>
					<button class="btn btn-xs btn-default text-danger ak-del-fu" title="${__("Remove")}">
						<svg class="icon icon-sm"><use href="#icon-close"></use></svg>
					</button>
				</div>
			`);

			$row.find(".ak-edit-fu").on("click", () => {
				_open_field_update_dialog(frm, u, action_idx, () =>
					_render_field_updates_html(frm, cdt, cdn)
				);
			});

			$row.find(".ak-del-fu").on("click", () => {
				frm.doc.field_updates = (frm.doc.field_updates || []).filter(
					(r) => r.name !== u.name
				);
				frm.dirty();
				frm.refresh_field("field_updates");
				_render_field_updates_html(frm, cdt, cdn);
			});

			$c.append($row);
		});
	} else {
		$c.append(
			'<div style="color:var(--text-muted); font-size:13px; padding:8px 0;">No field updates yet. Click the button below to add one.</div>'
		);
	}

	// Add button
	let $btn = $(`<button class="btn btn-sm btn-primary-light" style="margin-top:4px;">
		<svg class="icon icon-sm" style="margin-right:4px;"><use href="#icon-add"></use></svg>
		${__("Add Field Update")}
	</button>`);
	$btn.on("click", () => {
		_open_field_update_dialog(frm, null, action_idx, () =>
			_render_field_updates_html(frm, cdt, cdn)
		);
	});
	$c.append($btn);

	$w.append($c);
}

// ══════════════════════════════════════════════════════════
//  Single combined dialog: pick field + set value at once
// ══════════════════════════════════════════════════════════

function _open_field_update_dialog(frm, existing_row, action_idx, on_done) {
	if (!frm.__doctype_fields || !frm.__doctype_fields.length) {
		frappe.msgprint(__("Please select a Target Module (Reference DocType) first and save."));
		return;
	}

	let field_options = frm.__doctype_fields.map(
		(f) => `${f.fieldname}`
	);
	let field_labels = {};
	frm.__doctype_fields.forEach((f) => {
		field_labels[f.fieldname] = `${f.label} (${f.fieldname})`;
	});

	let is_edit = !!existing_row;
	let title = is_edit
		? __("Edit Field Update — {0}", [field_labels[existing_row.target_field] || existing_row.target_field])
		: __("Add Field Update");

	let d = new frappe.ui.Dialog({
		title: title,
		size: "large",
		fields: [
			// ── Field selector (hidden when editing) ──
			{
				fieldtype: "Autocomplete",
				fieldname: "target_field",
				label: __("Field"),
				options: field_options,
				reqd: 1,
				default: is_edit ? existing_row.target_field : "",
				read_only: is_edit ? 1 : 0,
				description: is_edit ? "" : "Start typing to search for a field",
			},
			{
				fieldtype: "Section Break",
			},
			// ── Value config ──
			{
				fieldtype: "Select",
				fieldname: "value_type",
				label: __("Set To"),
				options: "Static Value\nExpression\nUse Field\nUse Function\nToday\nToday + N Days\nToday - N Days\nCurrent User\nClear",
				default: is_edit ? (existing_row.value_type || "Static Value") : "Static Value",
				reqd: 1,
				change: function () {
					_toggle_dialog_fields(d);
				},
			},
			{
				fieldtype: "Column Break",
			},
			{
				fieldtype: "Autocomplete",
				fieldname: "source_field",
				label: __("Source Field"),
				options: field_options,
				default: is_edit ? (existing_row.source_field || "") : "",
				description: "Copy the value from this field",
			},
			{
				fieldtype: "Select",
				fieldname: "function_name",
				label: __("Function"),
				options: "\nconcat\nuppercase\nlowercase\ntrim\nlength\nround\nabs\nceil\nfloor",
				default: is_edit ? (existing_row.function_name || "") : "",
			},
			{
				fieldtype: "Section Break",
				fieldname: "sb_value",
			},
			{
				fieldtype: "Small Text",
				fieldname: "value",
				label: __("Value"),
				default: is_edit ? (existing_row.value || "") : "",
			},
			{
				fieldtype: "Int",
				fieldname: "days_offset",
				label: __("Number of Days"),
				default: is_edit ? (existing_row.days_offset || 0) : 0,
			},
			{
				fieldtype: "Section Break",
				fieldname: "sb_help",
			},
			{
				fieldtype: "HTML",
				fieldname: "help_html",
			},
		],
		primary_action_label: is_edit ? __("Update") : __("Add"),
		primary_action: function (values) {
			if (!values.target_field) {
				frappe.throw(__("Please select a field."));
				return;
			}

			let summary = _build_display_summary(values);

			if (is_edit) {
				// Update existing row
				frappe.model.set_value(existing_row.doctype, existing_row.name, {
					target_field: values.target_field,
					value_type: values.value_type,
					value: values.value || "",
					source_field: values.source_field || "",
					function_name: values.function_name || "",
					days_offset: values.days_offset || 0,
					display_summary: summary,
				});
			} else {
				// Create new row
				let row = frm.add_child("field_updates");
				frappe.model.set_value(row.doctype, row.name, {
					target_field: values.target_field,
					parent_action_idx: action_idx || 0,
					value_type: values.value_type,
					value: values.value || "",
					source_field: values.source_field || "",
					function_name: values.function_name || "",
					days_offset: values.days_offset || 0,
					display_summary: summary,
				});
			}

			frm.refresh_field("field_updates");
			frm.dirty();
			d.hide();
			if (on_done) on_done();
		},
	});

	// Format autocomplete display
	if (d.fields_dict.target_field && d.fields_dict.target_field.$input) {
		d.fields_dict.target_field.awesomplete.list = frm.__doctype_fields.map(
			(f) => ({ label: `${f.label} (${f.fieldname}) — ${f.fieldtype}`, value: f.fieldname })
		);
	}

	// Help HTML
	d.fields_dict.help_html.$wrapper.html(_get_help_html());

	// Initial field visibility toggle
	_toggle_dialog_fields(d);

	d.show();

	// Focus field selector for new, or value type for edit
	if (!is_edit && d.fields_dict.target_field.$input) {
		d.fields_dict.target_field.$input.focus();
	}
}

function _toggle_dialog_fields(d) {
	let vt = d.get_value("value_type");

	d.set_df_property("source_field", "hidden", 1);
	d.set_df_property("function_name", "hidden", 1);
	d.set_df_property("value", "hidden", 1);
	d.set_df_property("days_offset", "hidden", 1);
	d.set_df_property("sb_help", "hidden", 1);
	d.set_df_property("sb_value", "hidden", 1);

	switch (vt) {
		case "Static Value":
			d.set_df_property("sb_value", "hidden", 0);
			d.set_df_property("value", "hidden", 0);
			d.set_df_property("value", "label", __("Value"));
			break;
		case "Expression":
			d.set_df_property("sb_value", "hidden", 0);
			d.set_df_property("value", "hidden", 0);
			d.set_df_property("value", "label", __("Expression"));
			d.set_df_property("sb_help", "hidden", 0);
			break;
		case "Use Field":
			d.set_df_property("source_field", "hidden", 0);
			break;
		case "Use Function":
			d.set_df_property("source_field", "hidden", 0);
			d.set_df_property("function_name", "hidden", 0);
			break;
		case "Today + N Days":
		case "Today - N Days":
			d.set_df_property("sb_value", "hidden", 0);
			d.set_df_property("days_offset", "hidden", 0);
			break;
	}
}

// ══════════════════════════════════════════════════════════
//  Helpers
// ══════════════════════════════════════════════════════════

function _load_doctype_fields(frm) {
	frappe.call({
		method: "frappe_ak.api.automation.get_doctype_fields",
		args: { doctype: frm.doc.reference_doctype },
		callback: function (r) {
			if (r.message) {
				frm.__doctype_fields = r.message;
				let opts = r.message.map((f) => f.fieldname);
				frm.set_df_property("trigger_field", "options", [""].concat(opts).join("\n"));
				_update_condition_field_options(frm, opts);
				_update_field_update_options(frm, opts);
			}
		},
	});
}

function _update_condition_field_options(frm, opts) {
	let s = opts.join("\n");
	["all_conditions", "any_conditions"].forEach((tbl) => {
		let g = frm.fields_dict[tbl];
		if (g && g.grid) {
			g.grid.update_docfield_property("field", "options", s);
			g.grid.refresh();
		}
	});
}

function _update_field_update_options(frm, opts) {
	let g = frm.fields_dict.field_updates;
	if (g && g.grid) {
		let s = opts.join("\n");
		g.grid.update_docfield_property("target_field", "options", s);
		g.grid.update_docfield_property("source_field", "options", s);
		g.grid.refresh();
	}
}

function _set_child_field_options(frm, cdt, cdn, fieldname, options) {
	let grid_row = frm.fields_dict.all_conditions.grid.grid_rows_by_docname[cdn]
		|| frm.fields_dict.any_conditions.grid.grid_rows_by_docname[cdn];
	if (grid_row) {
		let field = grid_row.get_field(fieldname);
		if (field) {
			field.df.options = options.join("\n");
			field.refresh();
		}
	}
}

function _build_display_summary(values) {
	switch (values.value_type) {
		case "Static Value":
			return values.value ? `"${values.value}"` : '""';
		case "Expression":
			return values.value || "(empty)";
		case "Use Field":
			return values.source_field ? `= ${values.source_field}` : "(no field)";
		case "Use Function":
			return `${values.function_name || "?"}(${values.source_field || "?"})`;
		case "Today":
			return "Today";
		case "Today + N Days":
			return `Today + ${values.days_offset || 0} days`;
		case "Today - N Days":
			return `Today - ${values.days_offset || 0} days`;
		case "Current User":
			return "Current User";
		case "Clear":
			return "(Clear)";
		default:
			return values.value || "";
	}
}

function _get_help_html() {
	return `
	<div style="background:var(--subtle-fg); border:1px solid var(--border-color); border-radius:8px; padding:14px; font-size:12px; line-height:1.7;">
		<div style="font-weight:600; margin-bottom:6px;">Expression Syntax</div>
		<code style="display:block; white-space:pre-wrap; background:none; padding:0;">annual_revenue / 12
amount * 1.1
if status == 'Open' then 'Active' else 'Inactive' end</code>
		<div style="font-weight:600; margin-top:12px; margin-bottom:6px;">Functions</div>
		<code style="display:block; white-space:pre-wrap; background:none; padding:0;">concat(a, ' ', b)  uppercase(f)  lowercase(f)
trim(f)  length(f)  round(f, 2)  abs(f)</code>
		<div style="font-weight:600; margin-top:12px; margin-bottom:6px;">Variables</div>
		<code style="display:block; white-space:pre-wrap; background:none; padding:0;">doc.fieldname    frappe.session.user
today()    add_days(today(), 7)    now()</code>
	</div>`;
}
