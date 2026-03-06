app_name = "frappe_ak"
app_title = "Frappe AK"
app_publisher = "AK"
app_description = "AKCOM Ledger and Automation for Frappe"
app_email = "advait.k@swajal.in"
app_license = "MIT"
app_logo = "/assets/frappe_ak/images/ak_logo.svg"
required_apps = ["frappe"]

# Setup
after_install = "frappe_ak.setup.install.after_install"

# Document Events
doc_events = {
    "*": {
        "after_insert": "frappe_ak.dispatcher.engine.handle_event",
        "on_update": "frappe_ak.dispatcher.engine.handle_event",
        "on_submit": "frappe_ak.dispatcher.engine.handle_event",
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

# Scheduled Tasks
scheduler_events = {
    "all": [
        "frappe_ak.dispatcher.engine.run_cron_automations",
    ],
    "daily": [
        "frappe_ak.dispatcher.engine.cleanup_old_logs",
    ],
}
