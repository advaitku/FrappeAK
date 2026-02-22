app_name = "doc_designer_ak"
app_title = "Doc Designer AK"
app_publisher = "AK"
app_description = "Document Designer + Interactive Sharing for Frappe"
app_email = "ak@example.com"
app_license = "MIT"

# App includes (loaded on every Desk page)
app_include_js = [
    "/assets/doc_designer_ak/js/share_button.bundle.js"
]

# Jinja environment — register template helper functions
jenv = {
    "methods": [
        "doc_designer_ak.template_helpers.ak_input",
        "doc_designer_ak.template_helpers.ak_textarea",
        "doc_designer_ak.template_helpers.ak_date",
        "doc_designer_ak.template_helpers.ak_datetime",
        "doc_designer_ak.template_helpers.ak_checkbox",
        "doc_designer_ak.template_helpers.ak_select",
        "doc_designer_ak.template_helpers.ak_field_table",
        "doc_designer_ak.template_helpers.ak_items_table",
        "doc_designer_ak.template_helpers.ak_accept_decline",
        "doc_designer_ak.template_helpers.ak_submit_button",
    ]
}

# Document Events — auto-send triggers
doc_events = {
    "*": {
        "on_submit": "doc_designer_ak.api.check_auto_send",
        "on_update": "doc_designer_ak.api.check_auto_send",
        "after_insert": "doc_designer_ak.api.check_auto_send",
    }
}

# Sample data fixtures (loaded on bench migrate)
fixtures = [
    {
        "dt": "AK Document Template",
        "filters": [["template_name", "=", "Sales Order Approval"]]
    }
]

# Scheduled Tasks
scheduler_events = {
    "hourly": [
        "doc_designer_ak.tasks.expire_shares",
        "doc_designer_ak.tasks.send_reminders",
    ],
}
