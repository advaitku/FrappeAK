app_name = "automation_ak"
app_title = "AutomationAK"
app_publisher = "AK"
app_description = "Visual automation/workflow builder for Frappe Framework"
app_email = "ak@example.com"
app_license = "MIT"
app_logo = "/assets/automation_ak/images/ak_logo.svg"

# App includes (loaded on every Desk page)
app_include_js = [
    "/assets/automation_ak/js/ak_buttons.bundle.js"
]
app_include_css = [
    "/assets/automation_ak/css/automation_ak.css"
]

# Jinja environment — allow custom email templates
jenv = {
    "methods": [],
}

email_templates = [
    "automation_ak/templates/emails/default_notification.html"
]

# Document Events — wildcard dispatcher
doc_events = {
    "*": {
        "after_insert": "automation_ak.dispatcher.engine.handle_event",
        "on_update": "automation_ak.dispatcher.engine.handle_event",
        "before_save": "automation_ak.dispatcher.engine.handle_event",
        "on_submit": "automation_ak.dispatcher.engine.handle_event",
        "on_cancel": "automation_ak.dispatcher.engine.handle_event",
    }
}

# Scheduled Tasks
scheduler_events = {
    "cron": {
        "* * * * *": "automation_ak.dispatcher.engine.run_cron_automations",
    },
    "daily": [
        "automation_ak.dispatcher.engine.cleanup_old_logs",
    ],
}
