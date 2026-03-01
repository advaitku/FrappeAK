app_name = "frappe_ak"
app_title = "Frappe AK"
app_publisher = "AK"
app_description = "AKCOM Ledger and Document Designer for Frappe"
app_email = "advait.k@swajal.in"
app_license = "MIT"
app_logo = "/assets/frappe_ak/images/ak_logo.svg"
required_apps = ["frappe"]

# App includes (loaded on every Desk page)
app_include_js = [
    "/assets/frappe_ak/js/share_button.bundle.js",
]

# Setup
after_install = "frappe_ak.setup.install.after_install"

# Jinja environment — template helpers + custom email templates
jenv = {
    "methods": [
        "frappe_ak.template_helpers.ak_input",
        "frappe_ak.template_helpers.ak_textarea",
        "frappe_ak.template_helpers.ak_date",
        "frappe_ak.template_helpers.ak_datetime",
        "frappe_ak.template_helpers.ak_checkbox",
        "frappe_ak.template_helpers.ak_select",
        "frappe_ak.template_helpers.ak_field_table",
        "frappe_ak.template_helpers.ak_items_table",
        "frappe_ak.template_helpers.ak_accept_decline",
        "frappe_ak.template_helpers.ak_submit_button",
    ]
}

email_templates = [
    "frappe_ak/templates/emails/default_notification.html"
]

# Document Events
doc_events = {
    "*": {
        "after_insert": [
            "frappe_ak.doc_api.check_auto_send",
            "frappe_ak.dispatcher.engine.handle_event",
        ],
        "on_update": [
            "frappe_ak.doc_api.check_auto_send",
            "frappe_ak.dispatcher.engine.handle_event",
        ],
        "on_submit": [
            "frappe_ak.doc_api.check_auto_send",
            "frappe_ak.dispatcher.engine.handle_event",
        ],
    }
}

# AKCOM Permissions
has_permission = {
    "AKCOM Person": "frappe_ak.akcom.doctype.akcom_person.akcom_person.has_permission",
    "AKCOM Ledger Entry": "frappe_ak.akcom.doctype.akcom_ledger_entry.akcom_ledger_entry.has_permission",
}

permission_query_conditions = {
    "AKCOM Person": "frappe_ak.akcom.doctype.akcom_person.akcom_person.get_permission_query_conditions",
    "AKCOM Ledger Entry": "frappe_ak.akcom.doctype.akcom_ledger_entry.akcom_ledger_entry.get_permission_query_conditions",
}

# Fixtures
fixtures = [
    {
        "dt": "AK Document Template",
        "filters": [["template_name", "=", "Sales Order Approval"]]
    }
]

# Scheduled Tasks
scheduler_events = {
    "all": [
        "frappe_ak.dispatcher.engine.run_cron_automations",
    ],
    "hourly": [
        "frappe_ak.tasks.expire_shares",
        "frappe_ak.tasks.send_reminders",
    ],
    "daily": [
        "frappe_ak.dispatcher.engine.cleanup_old_logs",
    ],
}
