# CLAUDE.md — Frappe Ecosystem Developer Reference

> This file provides context and conventions for AI-assisted development across ERPNext, Frappe Helpdesk, and Frappe CRM. Read this before creating any files, doctypes, scripts, or components.

---

## Project Overview

This project operates within the **Frappe Framework ecosystem**. The three primary applications are:

- **ERPNext** (a.k.a. "NextERP") — Full-featured ERP (accounting, sales, inventory, HR, manufacturing). Uses Frappe Desk (jQuery) frontend.
- **Frappe Helpdesk** — Customer service/ticketing platform. Uses Vue 3 SPA frontend (`desk/` directory).
- **Frappe CRM** — Sales pipeline/lead management. Uses Vue 3 + Pinia SPA frontend (`frontend/` directory).

All three share the same Python backend architecture, DocType data model, and bench CLI tooling. The divergence is in the frontend layer.

---

## Tech Stack

| Component          | Technology                                              |
| ------------------ | ------------------------------------------------------- |
| Backend            | Python 3.10+                                            |
| Database           | MariaDB (primary), PostgreSQL (supported)               |
| Caching/Queue      | Redis (cache, queue, real-time)                         |
| Task Queue         | Python RQ                                               |
| Real-time          | Socket.IO (WebSockets)                                  |
| Web Server         | Werkzeug (dev), Gunicorn + Nginx (prod)                 |
| CLI                | Bench (`bench start`, `bench migrate`, etc.)            |
| Package Management | pip (Python), Yarn (JavaScript)                         |
| Build System       | Vite (Helpdesk/CRM), Rollup/esbuild (ERPNext Desk)     |
| Frontend (ERPNext) | jQuery + Jinja2 (Frappe Desk)                           |
| Frontend (Helpdesk)| Vue 3 + TypeScript + Frappe UI composables + Tailwind   |
| Frontend (CRM)     | Vue 3 + Pinia + Frappe UI + Tailwind + Twilio Voice SDK |

---

## Directory Structure

### Bench (top-level workspace)

```
frappe-bench/
├── apps/                         # All Frappe apps
│   ├── frappe/                   # Core framework
│   ├── erpnext/                  # ERPNext app
│   ├── helpdesk/                 # Helpdesk app
│   └── crm/                     # CRM app
├── config/                       # Redis config files
├── env/                          # Python virtual environment
├── logs/                         # Application logs
├── Procfile                      # Process definitions
└── sites/
    ├── apps.txt                  # Installed apps list
    ├── common_site_config.json
    └── {site_name}/
        ├── site_config.json      # DB credentials, per-site settings
        ├── private/              # Private file uploads
        └── public/               # Public file uploads
```

### ERPNext App Structure

```
apps/erpnext/erpnext/
├── hooks.py
├── modules.txt                   # ~25 modules
├── patches.txt                   # Migration patches
├── accounts/doctype/             # GL, invoices, payments
├── selling/doctype/              # Sales orders, quotations
├── buying/doctype/               # Purchase orders, RFQs
├── stock/doctype/                # Warehouses, stock entries
├── manufacturing/doctype/        # BOMs, work orders
├── hr/doctype/                   # Employees, attendance, payroll
├── projects/doctype/             # Tasks, timesheets
├── assets/doctype/               # Fixed asset management
├── setup/doctype/                # Company, naming series
├── support/doctype/              # Issues, SLAs
├── regional/                     # Country-specific tax/compliance
├── public/                       # Static CSS/JS
├── templates/                    # Jinja2 templates
└── www/                          # Portal web pages
```

### Helpdesk App Structure

```
apps/helpdesk/
├── desk/                         # ★ Vue 3 SPA frontend
│   ├── src/
│   │   ├── components/           # Reusable Vue components
│   │   ├── pages/                # Page-level route components
│   │   └── router/               # Vue Router config
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── index.html
├── helpdesk/                     # ★ Python backend
│   ├── hooks.py
│   ├── api/                      # @frappe.whitelist() endpoints
│   ├── helpdesk/doctype/         # All HD-prefixed DocTypes
│   │   ├── hd_ticket/
│   │   ├── hd_team/
│   │   ├── hd_settings/
│   │   ├── hd_service_level_agreement/
│   │   ├── hd_ticket_status/
│   │   ├── hd_ticket_type/
│   │   ├── hd_ticket_priority/
│   │   ├── hd_assignment_rule/
│   │   ├── hd_email_feedback/
│   │   └── hd_article/
│   ├── search.py                 # Redis Search integration
│   └── extends/                  # Extensibility modules
└── frappe-ui/                    # Git submodule
```

### CRM App Structure

```
apps/crm/
├── frontend/                     # ★ Vue 3 SPA
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router.js
│   │   ├── socket.js             # WebSocket connection
│   │   ├── pages/                # Leads, Deals, Contacts, etc.
│   │   ├── components/
│   │   │   ├── Activities/       # Email, calls, WhatsApp timeline
│   │   │   ├── Controls/         # Custom form inputs
│   │   │   ├── Icons/            # 80+ SVG icon components
│   │   │   ├── Kanban/           # Kanban board view
│   │   │   ├── Layouts/          # Desktop/Mobile layouts
│   │   │   ├── ListViews/        # Entity-specific lists
│   │   │   ├── Modals/           # Create/edit dialogs
│   │   │   └── Settings/         # Settings pages
│   │   ├── stores/               # ★ Pinia stores
│   │   ├── composables/          # Vue composables
│   │   └── utils/
│   ├── package.json              # frappe-ui, pinia, vue-router, @twilio/voice-sdk
│   ├── vite.config.js
│   └── tailwind.config.js
├── crm/                          # ★ Python backend
│   ├── hooks.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── doc.py
│   ├── fcrm/doctype/             # All CRM-prefixed DocTypes
│   │   ├── crm_lead/
│   │   ├── crm_deal/
│   │   ├── crm_organization/
│   │   ├── crm_lead_status/
│   │   ├── crm_deal_status/
│   │   ├── crm_notification/
│   │   ├── crm_settings/
│   │   ├── crm_form_script/
│   │   └── crm_fields_layout/
│   ├── www/crm.html              # Built SPA entry point
│   ├── public/frontend/          # Built Vite output
│   ├── overrides/
│   ├── patches/
│   └── fixtures/
└── frappe-ui/                    # Git submodule
```

---

## Golden Rules

1. **Never modify ERPNext or Frappe source directly.** Always create a custom app.
2. **DocType naming conventions matter:**
   - ERPNext: descriptive names, no prefix (e.g., `Sales Order`, `Purchase Invoice`)
   - Helpdesk: `HD` prefix (e.g., `HD Ticket`, `HD Team`)
   - CRM: `CRM` prefix (e.g., `CRM Lead`, `CRM Deal`)
3. **Backend patterns are identical across all three.** DocTypes, hooks.py, controllers, whitelisted methods, and bench CLI work the same everywhere.
4. **Frontend patterns diverge completely:**
   - ERPNext → `frappe.ui.form.on()` + `.js` files
   - Helpdesk → Vue 3 + TypeScript + Frappe UI composables (no Pinia)
   - CRM → Vue 3 + Pinia stores + class-based CRM Form Scripts
5. **Always run `bench --site {site} migrate` after DocType schema changes.**

---

## Architecture — How Frappe Differs From Other Frameworks

Frappe is **not** Flask, Django, FastAPI, or any conventional MVC framework. It is a **metadata-driven** full-stack framework where the DocType (a JSON schema) simultaneously defines the database table, the ORM model, the REST API, the form UI, the list view, permissions, and search behavior. **Declarative configuration replaces imperative code** for most tasks.

**Key architectural truths:**

- **Everything is a DocType.** Users, roles, permissions, settings, error logs, scheduled jobs — all DocTypes. There is no separate ORM layer, no `models.py`, no migrations directory. The DocType JSON *is* the schema.
- **The bench CLI manages everything.** There is no `manage.py`, no `flask run`, no standalone `pip install`. The `bench` tool manages sites, apps, virtual environments, process supervision, database operations, and builds.
- **Apps contain modules, modules contain DocTypes.** The directory hierarchy is rigid and enforced. Files in the wrong location are silently ignored.
- **The Desk (admin UI) is jQuery-based**, not React or Vue. "Frappe UI" is a separate Vue 3 component library used only by standalone apps (CRM, Helpdesk, Insights) — it does **not** power the main Desk.
- **Two routing domains exist**: the Desk SPA at `/app/*` (v15) or `/desk/*` (v16) for authenticated users, and the website/portal at root routes for public pages.

---

## DocType Development

### File Structure (all apps)

Every DocType directory must contain:

```
module_name/doctype/my_doctype/
├── my_doctype.json          # Schema: fields, permissions, settings
├── my_doctype.py            # Python controller (extends Document)
├── my_doctype.js            # Client-side form script (optional, ERPNext only)
└── test_my_doctype.py       # Unit tests
```

Database tables are auto-created prefixed with `tab` (e.g., `tabSales Order`, `tabHD Ticket`).

### DocType JSON Schema — Exact Format

Every DocType is defined by a `.json` file. Here is the complete structure:

```json
{
  "name": "My DocType",
  "module": "My Module",
  "doctype": "DocType",
  "naming_rule": "By fieldname",
  "autoname": "field:title",
  "title_field": "title",
  "search_fields": "status,customer",
  "sort_field": "creation",
  "sort_order": "DESC",
  "is_submittable": 0,
  "istable": 0,
  "issingle": 0,
  "is_tree": 0,
  "is_virtual": 0,
  "editable_grid": 1,
  "track_changes": 1,
  "has_web_view": 0,
  "allow_rename": 0,
  "quick_entry": 0,
  "field_order": ["title", "status", "section_break_1", "description"],
  "fields": [
    {
      "fieldname": "title",
      "fieldtype": "Data",
      "label": "Title",
      "reqd": 1,
      "in_list_view": 1,
      "in_global_search": 1
    },
    {
      "fieldname": "status",
      "fieldtype": "Select",
      "label": "Status",
      "options": "Open\nIn Progress\nCompleted",
      "default": "Open",
      "in_list_view": 1,
      "in_standard_filter": 1
    },
    {
      "fieldname": "section_break_1",
      "fieldtype": "Section Break"
    },
    {
      "fieldname": "description",
      "fieldtype": "Text Editor",
      "label": "Description"
    }
  ],
  "permissions": [
    {
      "role": "System Manager",
      "read": 1, "write": 1, "create": 1, "delete": 1,
      "submit": 0, "cancel": 0, "amend": 0,
      "report": 1, "export": 1, "import": 1,
      "print": 1, "email": 1, "share": 1,
      "permlevel": 0
    }
  ],
  "links": [],
  "actions": [],
  "states": []
}
```

**All valid fieldtype values** (never invent new ones):

- **Data types**: `Data`, `Int`, `Float`, `Currency`, `Percent`, `Check`, `Small Text`, `Long Text`, `Text`, `Text Editor`, `Code`, `HTML Editor`, `Markdown Editor`, `Password`, `Read Only`, `JSON`
- **Link/relation**: `Link` (options = target DocType), `Dynamic Link` (options = fieldname holding DocType), `Table` (options = child DocType), `Table MultiSelect`
- **Selection**: `Select` (options are `\n`-separated strings, NOT arrays), `Rating`, `Color`, `Autocomplete`, `Icon`
- **Date/time**: `Date`, `Datetime`, `Time`, `Duration`
- **Attachment**: `Attach`, `Attach Image`, `Image`, `Signature`
- **Layout** (no DB column): `Section Break`, `Column Break`, `Tab Break`, `Fold`
- **Special**: `Barcode`, `Geolocation`, `Heading`, `HTML`, `Button`, `Phone`

**Autoname/naming patterns** (set via `autoname` property):

- `field:fieldname` — name equals the field's value
- `naming_series:` — uses the Naming Series field (e.g., `INV-.YYYY.-.#####`)
- `format:PREFIX-{field1}-{####}` — template with counters
- `hash` — random hash
- `autoincrement` — auto-incrementing integer
- `prompt` — user enters name manually
- `UUID` — UUID v7 (v16+)
- Controller `def autoname(self):` method for programmatic naming

**Auto-added columns** (always present, never define in `fields` array): `name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus` (0=Draft, 1=Submitted, 2=Cancelled), `idx`.

**Critical naming rules**: DocType directory names use **snake_case** matching the DocType's `name` lowercased with spaces replaced by underscores. The Python class name is **PascalCase**. The JSON file, Python file, and JS file all share the snake_case name. Getting any of these wrong causes silent failures.

### Controller Lifecycle Events (in order)

**Insert**: `autoname` → `before_insert` → `before_validate` → `validate` → `before_save` → DB INSERT → `after_insert` → `on_update` → `on_change`

**Update**: `before_validate` → `validate` → `before_save` → DB UPDATE → `on_update` → `on_change`

**Submit**: `before_submit` → `on_submit` → `on_update` → `on_change`

### Python Controller Template

```python
import frappe
from frappe.model.document import Document

class MyDoctype(Document):
    def autoname(self):
        """Set self.name before insert"""
        self.name = f"MY-{frappe.generate_hash(length=8)}"

    def before_insert(self):
        """Before first save only"""
        pass

    def after_insert(self):
        """After first save — document exists in DB"""
        pass

    def before_validate(self):
        """Before validation on both insert and update"""
        pass

    def validate(self):
        """Validation logic — runs on both insert and update"""
        if not self.required_field:
            frappe.throw("Required field is mandatory")

    def before_save(self):
        """After validate, before DB write"""
        self.computed_field = self.qty * self.rate

    def on_update(self):
        """After DB write (both insert and update)"""
        pass

    def before_submit(self):
        """Before docstatus changes to 1"""
        pass

    def on_submit(self):
        """After docstatus changes to 1"""
        self.create_related_records()

    def before_cancel(self):
        """Before docstatus changes to 2"""
        pass

    def on_cancel(self):
        """After docstatus changes to 2"""
        self.reverse_related_records()

    def on_trash(self):
        """Before deletion"""
        pass

    def after_delete(self):
        """After deletion"""
        pass

    def on_change(self):
        """On any change including workflow state"""
        pass
```

**Useful controller utilities:**
```python
old_doc = self.get_doc_before_save()   # Previous state in validate/on_update
self.has_value_changed("status")        # Check if field changed
self.is_new()                           # True only during insert flow
```

### Whitelisted API Methods

```python
@frappe.whitelist()
def my_custom_method(doctype, name, **kwargs):
    """Callable via POST /api/method/my_app.module.my_custom_method"""
    doc = frappe.get_doc(doctype, name)
    doc.check_permission("write")
    # ... do work ...
    return {"status": "ok"}

@frappe.whitelist(allow_guest=True)
def public_endpoint():
    """Accessible without authentication."""
    return {"message": "hello"}
```

### Frappe ORM — Complete Reference

**Never use SQLAlchemy, Django ORM, or raw DB connection patterns.** Use only these Frappe APIs:

#### Document Operations
```python
# Retrieve
doc = frappe.get_doc("Task", "TASK-001")          # Full document with child tables
doc = frappe.get_cached_doc("Company", "My Co")    # Cached for frequently-read docs

# Create
doc = frappe.new_doc("Task")
doc.title = "New Task"
doc.insert()

# Or in one expression:
doc = frappe.get_doc({"doctype": "Task", "title": "New Task", "items": [
    {"item_code": "ITEM-001", "qty": 5}
]}).insert()

# Lifecycle
doc.save()        # UPDATE — runs validate, on_update
doc.submit()      # Set docstatus=1
doc.cancel()      # Set docstatus=2
doc.delete()      # DELETE
doc.reload()      # Re-read from DB

# Direct DB update (bypasses ORM hooks):
doc.db_set("status", "Paid", notify=True, commit=True)

# Child tables
doc.append("items", {"item_code": "ITEM-001", "qty": 5, "rate": 100})

# Flags (pass state between hooks)
doc.flags.ignore_permissions = True
doc.flags.ignore_validate = True
doc.flags.ignore_mandatory = True
doc.insert()
```

#### Querying — Use the Right Method

**`frappe.db.get_value()`** — for fetching one or few fields from a single record:
```python
status = frappe.db.get_value("Task", "TASK-001", "status")
name, status = frappe.db.get_value("Task", "TASK-001", ["name", "status"])
email = frappe.db.get_value("User", {"first_name": "John"}, "email")
result = frappe.db.get_value("Task", {"status": "Open"}, ["name", "status"], as_dict=True)
```

**`frappe.db.get_single_value()`** — for Single DocTypes (v15+ REQUIRED):
```python
timezone = frappe.db.get_single_value("System Settings", "time_zone")
```

**`frappe.get_all()`** — list query WITHOUT permission checks (backend use):
```python
frappe.get_all("Task",
    filters={"status": "Open"},
    or_filters={"priority": ["in", ["High", "Urgent"]]},
    fields=["name", "subject", "date"],
    order_by="date desc",
    page_length=20,
    pluck="name",        # Returns flat list of one field
    distinct=True,
    debug=True           # Print SQL
)
```

**`frappe.get_list()`** — same API but WITH user permission checks. Use for user-facing queries.

**Filter syntax:**
```python
# Dict (equality, AND):
{"status": "Open", "customer": "CUST-001"}
# Dict with operators:
{"date": [">", "2024-01-01"], "status": ["in", ["Open", "Working"]]}
# List of lists:
[["date", "between", ["2024-01-01", "2024-12-31"]],
 ["subject", "like", "%test%"],
 ["assigned_to", "is", "set"]]       # not null/empty
```

**`frappe.db.set_value()`** — direct update (NOT for Single DocTypes in v15+):
```python
frappe.db.set_value("Task", "TASK-001", "status", "Completed")
frappe.db.set_value("Task", "TASK-001", {"status": "Done", "completed_on": frappe.utils.now()})
```

**`frappe.db.set_single_value()`** — for Single DocTypes:
```python
frappe.db.set_single_value("System Settings", "setup_complete", 1)
```

**Other essential methods:**
```python
frappe.db.exists("Task", "TASK-001")                    # Boolean
frappe.db.exists("Task", {"status": "Open"})
frappe.db.count("Task", filters={"status": "Open"})
frappe.db.sql("SELECT name FROM `tabTask` WHERE status=%s", "Open", as_dict=True)
frappe.db.delete("Error Log", {"creation": ("<", "2024-01-01")})
frappe.db.commit()         # Usually auto-committed at request end
frappe.rename_doc("Task", "OLD-001", "NEW-001")
frappe.delete_doc("Task", "TASK-001")
frappe.get_meta("Task")    # DocType metadata
```

**Critical anti-patterns:**
- **Do NOT** use `frappe.get_doc()` just to read a single field value — it loads the entire document with all child tables. Use `frappe.db.get_value()` instead.
- **Do NOT** use `frappe.db.set_value()` for Single DocTypes — use `frappe.db.set_single_value()`.
- **Table naming in raw SQL**: Always use backtick-quoted `tab` prefix: `` `tabSales Invoice` ``. Never use bare table names.
- **Always use parameterized queries** with `%s` or `%(name)s` in `frappe.db.sql()` — never string formatting.

---

## Query Builder (v16 Critical Changes)

In v16, **`frappe.get_all()` and `frappe.get_list()` internally use the Pypika-based Query Builder**, which breaks raw SQL expressions in fields:

```python
# BROKEN in v16:
frappe.get_all("Stock Ledger Entry", fields=["sum(actual_qty) as total"])

# CORRECT — dict-based syntax:
frappe.get_all("Stock Ledger Entry", fields=[{"SUM": "actual_qty", "as": "total"}])

# CORRECT — Pypika functions:
from frappe.query_builder.functions import Sum
sle = frappe.qb.DocType("Stock Ledger Entry")
frappe.get_all("Stock Ledger Entry", fields=[Sum(sle.actual_qty).as_("total")])
```

**Direct Query Builder usage:**
```python
Task = frappe.qb.DocType("Task")
query = (
    frappe.qb.from_(Task)
    .select(Task.name, Task.subject, Task.status)
    .where(Task.status == "Open")
    .orderby(Task.creation, order=frappe.qb.desc)
    .limit(10)
)
results = query.run(as_dict=True)
```

---

## REST API Reference

```
# CRUD operations
GET    /api/resource/{DocType}                    # List
POST   /api/resource/{DocType}                    # Create
GET    /api/resource/{DocType}/{name}             # Read
PUT    /api/resource/{DocType}/{name}             # Update
DELETE /api/resource/{DocType}/{name}             # Delete

# Custom methods
POST   /api/method/{dotted.path.to.function}      # Call whitelisted method

# Authentication options:
# 1. Cookie-based sessions (default for browser)
# 2. Token: Authorization: token {api_key}:{api_secret}
# 3. OAuth 2.0

# Common query params for list:
# ?filters=[["status","=","Open"]]
# &fields=["name","subject"]
# &order_by=modified desc
# &limit_page_length=20
# &limit_start=0
```

---

## Background Jobs

```python
frappe.enqueue(
    "my_app.tasks.long_task",
    queue="default",           # "short", "default", "long"
    timeout=300,
    job_id="unique_id",
    customer_name="Acme"       # kwargs passed to function
)

# Realtime progress:
frappe.publish_realtime("task_progress", {"percent": 50}, user=frappe.session.user)
```

**Important**: `frappe.db.commit()` is NOT auto-called in background jobs — you must call it explicitly after DB writes in enqueued functions.

---

## hooks.py Reference

The central configuration file for every Frappe app. Key sections:

```python
app_name = "my_app"
app_title = "My App"
app_publisher = "My Company"

# DocType event handlers (hook into ANY doctype without modifying it)
doc_events = {
    "Sales Order": {
        "validate": "my_app.overrides.sales_order.validate",
        "on_submit": "my_app.overrides.sales_order.on_submit",
    },
    "HD Ticket": {
        "after_insert": "my_app.overrides.ticket.after_insert",
    },
    "*": {
        "on_update": "my_app.utils.log_all_updates",  # All doctypes
    },
}

# Scheduled tasks
scheduler_events = {
    "daily": ["my_app.tasks.daily_cleanup"],
    "hourly": ["my_app.tasks.sync_data"],
    "cron": {
        "0 9 * * 1": "my_app.tasks.monday_report",  # Every Monday 9 AM
    },
}

# Website route rules (for SPA apps)
website_route_rules = [
    {"from_route": "/my-app/<path:app_path>", "to_route": "my-app"},
]

# Fixtures (export customizations as JSON for version control)
fixtures = [
    {"dt": "Custom Field", "filters": [["module", "=", "My App"]]},
    {"dt": "Property Setter", "filters": [["module", "=", "My App"]]},
]

# Override whitelisted methods
override_whitelisted_methods = {
    "frappe.client.get_count": "my_app.overrides.custom_get_count",
}

# Override DocType class
override_doctype_class = {
    "ToDo": "my_app.overrides.CustomToDo"
}

# Jinja environment customization
jinja = {
    "methods": ["my_app.utils.my_jinja_method"],
    "filters": ["my_app.utils.my_jinja_filter"],
}

# Asset injection
app_include_js = ["my_feature.bundle.js"]        # Desk — use .bundle.js naming
app_include_css = ["my_style.bundle.css"]
web_include_js = ["my_web.bundle.js"]            # Website/portal
doctype_js = {"Sales Invoice": "public/js/sales_invoice.js"}
doctype_list_js = {"Sales Invoice": "public/js/sales_invoice_list.js"}

# Permission hooks
permission_query_conditions = {
    "Task": "my_app.permissions.task_conditions"
}
# def task_conditions(user): return "(`tabTask`.owner = '{user}')"

has_permission = {
    "Task": "my_app.permissions.task_permission"
}
# def task_permission(doc, ptype, user): return True  # MUST return True explicitly in v16

# Lifecycle hooks
required_apps = ["frappe"]
after_install = "my_app.setup.after_install"
before_uninstall = "my_app.setup.before_uninstall"
boot_session = "my_app.boot.boot_session"
```

Export fixtures with `bench --site sitename export-fixtures`. Auto-imported on `bench migrate`.

---

## ERPNext (Desk) Frontend Patterns

### Client Script Pattern

```javascript
frappe.ui.form.on('Sales Order', {
    // Runs on form load/refresh
    refresh(frm) {
        if (frm.doc.docstatus === 1) {
            frm.add_custom_button(__('Create Invoice'), () => {
                frappe.call({
                    method: 'erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice',
                    args: { source_name: frm.doc.name },
                    callback: (r) => frappe.set_route('Form', 'Sales Invoice', r.message.name)
                });
            }, __('Create'));
        }
    },

    // Triggered when field value changes
    customer(frm) {
        if (frm.doc.customer) {
            frappe.call({
                method: 'erpnext.selling.utils.get_customer_details',
                args: { customer: frm.doc.customer },
                callback: (r) => {
                    frm.set_value('territory', r.message.territory);
                }
            });
        }
    },

    // Validate before save
    validate(frm) {
        if (frm.doc.grand_total < 0) {
            frappe.throw(__('Grand Total cannot be negative'));
        }
    }
});

// Child table events
frappe.ui.form.on('Sales Order Item', {
    item_code(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        // React to item changes in child table
    },
    qty(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        frappe.model.set_value(cdt, cdn, 'amount', row.qty * row.rate);
    }
});
```

### Useful `frm` Methods

```javascript
frm.set_value('field', value)              // Set field value
frm.set_query('link_field', () => {        // Filter link field options
    return { filters: { company: frm.doc.company } }
})
frm.add_custom_button(label, action, group) // Add toolbar button
frm.toggle_display('field', condition)       // Show/hide field
frm.set_df_property('field', 'reqd', 1)     // Make field mandatory
frm.refresh_field('field')                   // Re-render field
frm.trigger('field_name')                    // Trigger field handler
frm.save()                                   // Save document
frm.call('method_name', args)                // Call server method
```

### JavaScript APIs for Server Calls

```javascript
// RPC call to whitelisted method
frappe.call({
    method: "my_app.api.get_data",
    args: { customer: "CUST-001" },
    freeze: true,
    callback(r) { console.log(r.message); }
});

// Promise-based (preferred):
let result = await frappe.xcall("my_app.api.get_data", { customer: "CUST-001" });

// Client-side DB:
await frappe.db.get_value("Customer", "CUST-001", "territory");
await frappe.db.get_list("Task", { filters: { status: "Open" }, fields: ["name"] });
await frappe.db.set_value("Task", "TASK-001", "status", "Done");
```

---

## Helpdesk (Vue 3) Frontend Patterns

### Data Fetching — Frappe UI Composables (NO Pinia)

```javascript
import { createDocumentResource, createListResource, createResource } from "frappe-ui";

// Single document
const ticket = createDocumentResource({
    doctype: "HD Ticket",
    name: ticketId,
    auto: true,    // Fetch immediately
});
// Access: ticket.doc.subject, ticket.doc.status
// Update: ticket.setValue("status", "Resolved")

// List of documents
const tickets = createListResource({
    doctype: "HD Ticket",
    filters: { status: "Open" },
    fields: ["name", "subject", "modified"],
    orderBy: "modified desc",
    pageLength: 20,
    auto: true,
});
// Access: tickets.data

// Custom API call
const api = createResource({
    url: "helpdesk.api.ticket.assign_ticket",
    onSuccess(data) { /* handle response */ },
    onError(err) { /* handle error */ },
});
api.submit({ ticket_id: id, agent_id: agentId });
```

### Vue Component Template

```vue
<template>
  <div class="bg-surface-white border border-outline-gray-2 rounded-lg p-4">
    <h2 class="text-lg text-ink-gray-9 font-semibold">{{ ticket.doc?.subject }}</h2>
    <p class="text-sm text-ink-gray-6 mt-1">{{ ticket.doc?.description }}</p>
    <LucideTicket class="size-4 text-ink-gray-6" />
  </div>
</template>

<script setup lang="ts">
import { createDocumentResource } from "frappe-ui";
import LucideTicket from "~icons/lucide/ticket";

const props = defineProps<{ ticketId: string }>();

const ticket = createDocumentResource({
    doctype: "HD Ticket",
    name: props.ticketId,
    auto: true,
});
</script>
```

### Tailwind CSS Conventions (Helpdesk-specific)

Use **semantic gray-scale classes only** — never raw color shades, even for primary states:

```
Backgrounds:  bg-surface-white, bg-surface-gray-1 through bg-surface-gray-7
Text:         text-ink-gray-1 through text-ink-gray-9
Borders:      border-outline-gray-1 through border-outline-gray-5
```

Icons use **Lucide** via unplugin-icons:

```javascript
import LucidePlus from "~icons/lucide/plus";
import LucideSearch from "~icons/lucide/search";
```

---

## CRM (Vue 3 + Pinia) Frontend Patterns

### Pinia Store Pattern

```javascript
// frontend/src/stores/statuses.js
import { defineStore } from 'pinia';
import { createListResource } from 'frappe-ui';
import { reactive } from 'vue';

export const statusesStore = defineStore('crm-statuses', () => {
    let leadStatusesByName = reactive({});

    const leadStatuses = createListResource({
        doctype: 'CRM Lead Status',
        fields: ['name', 'color', 'position'],
        orderBy: 'position asc',
        cache: 'lead-statuses',
        auto: true,
        transform(statuses) {
            for (let s of statuses) leadStatusesByName[s.name] = s;
            return statuses;
        },
    });

    return { leadStatuses, leadStatusesByName };
});
```

### CRM Form Scripts (class-based, stored in DB)

These are **NOT** file-based. Create them as `CRM Form Script` DocType records:

```javascript
class CRMLead {
    onload() {
        // Runs when a saved record loads
        console.log(this.doc.lead_name);
    }

    status(value) {
        // Triggered when the 'status' field changes
        if (value === 'Converted') {
            this.call('crm.api.some_method', { lead: this.doc.name });
        }
    }
}
```

Key differences from ERPNext scripts:
- Stored in database, not files
- Class-based syntax (not `frappe.ui.form.on()`)
- No asset rebuild required
- `this.doc` accesses the current document
- Method names match field names to react to changes
- `this.call()` invokes server methods

### CRM Key DocTypes

| DocType              | Purpose                                       |
| -------------------- | --------------------------------------------- |
| CRM Lead             | Prospect/potential customer                    |
| CRM Deal             | Sales opportunity (converted from lead)        |
| CRM Organization     | Company/organization entity                    |
| CRM Lead Status      | Configurable lead statuses (color, position)   |
| CRM Deal Status      | Configurable deal statuses (color, position)   |
| CRM Notification     | In-app notifications                           |
| CRM Settings         | App-wide configuration                         |
| CRM Form Script      | Class-based UI customization scripts           |
| CRM Fields Layout    | Custom field layout definitions                |

CRM also reuses standard Frappe DocTypes: **Contact**, **Note**, **Task**, **Call Log**, **Email Template**, **Communication**, **Comment**.

---

## App Versioning — Required for Bench to Function

Every Frappe app **must** declare its version in two places. Missing or mismatched versions cause `bench install-app`, `bench migrate`, and `bench update` to fail.

**1. `my_app/__init__.py`** — the single source of truth:
```python
__version__ = "0.0.1"
```

**2. `pyproject.toml`** — must reference it dynamically:
```toml
[project]
name = "my_app"
dynamic = ["version"]

[tool.flit.module]
name = "my_app"
```

**Rules:**

- **Always include `__version__` in `__init__.py`** — bench reads this at install time and during migrations. Without it, you get `AttributeError: module 'my_app' has no attribute '__version__'`.
- **Never hardcode the version in `pyproject.toml`** — use `dynamic = ["version"]` so flit reads it from `__init__.py`. Two hardcoded versions will drift.
- **Use semantic versioning** (`MAJOR.MINOR.PATCH`) — Frappe's dependency resolver expects this format.
- **Bump the version before running `bench migrate`** when your app includes new patches — bench uses the version to determine which patches to run.
- **Never delete or rename `__init__.py`** in the app's root module directory — it breaks the entire app import chain.
- **If adding Frappe app dependencies**, pin them in `pyproject.toml`:
```toml
[tool.bench.frappe-dependencies]
frappe = ">=16.0.0,<17.0.0"
erpnext = ">=16.0.0,<17.0.0"
```

**Common AI mistake**: generating a new app or module without touching `__init__.py`, or creating a `setup.py` with a hardcoded `version="1.0.0"` that conflicts with `__init__.py`. Both break bench.

---

## Creating a Custom App

```bash
# 1. Create the app scaffold
bench new-app my_custom_app

# 2. Install on your site
bench --site mysite install-app my_custom_app

# 3. Generated structure:
# apps/my_custom_app/
# ├── my_custom_app/
# │   ├── __init__.py
# │   ├── hooks.py           # ← Configure doc_events, scheduler, etc.
# │   ├── modules.txt        # ← List your modules here
# │   ├── patches.txt        # ← Migration patches
# │   └── my_module/
# │       ├── __init__.py
# │       └── doctype/       # ← Your custom DocTypes go here
# ├── pyproject.toml
# ├── setup.py
# └── package.json
```

### Extending Existing DocTypes (via hooks.py)

```python
# my_custom_app/hooks.py
doc_events = {
    "Sales Order": {
        "validate": "my_custom_app.overrides.sales_order.custom_validate",
        "on_submit": "my_custom_app.overrides.sales_order.custom_on_submit",
    },
}
```

```python
# my_custom_app/overrides/sales_order.py
import frappe

def custom_validate(doc, method):
    """doc is the Sales Order document instance."""
    if doc.grand_total > 100000:
        frappe.msgprint("Large order — manager approval may be required.")

def custom_on_submit(doc, method):
    # Create follow-up task on submission
    frappe.get_doc({
        "doctype": "ToDo",
        "description": f"Follow up on {doc.name}",
        "reference_type": "Sales Order",
        "reference_name": doc.name,
    }).insert()
```

---

## Common CLI Commands

```bash
# Start development server
bench start

# Create new site
bench new-site mysite.localhost

# Install app on site
bench --site mysite install-app erpnext

# Run database migrations after schema changes
bench --site mysite migrate

# Open Python console with Frappe context
bench --site mysite console

# Open MariaDB console
bench --site mysite mariadb

# Clear cache
bench --site mysite clear-cache

# Export fixtures
bench --site mysite export-fixtures

# Run tests
bench --site mysite run-tests --app my_app
bench --site mysite run-tests --doctype "My DocType"

# Build frontend assets
bench build --app helpdesk
bench build --app crm

# Frontend dev servers
cd apps/helpdesk/desk && yarn dev       # Helpdesk at :8080
cd apps/crm/frontend && yarn dev        # CRM at :8080
```

---

## Quick Comparison Table

| Aspect               | ERPNext                          | Helpdesk                              | CRM                                       |
| -------------------- | -------------------------------- | ------------------------------------- | ----------------------------------------- |
| Frontend             | Frappe Desk (jQuery + Jinja2)    | Vue 3 SPA                            | Vue 3 SPA                                |
| Frontend dir         | N/A (built into Frappe)          | `desk/`                               | `frontend/`                               |
| State management     | N/A                              | Frappe UI composables (no store)      | Pinia stores                              |
| Client scripts       | `frappe.ui.form.on()` in `.js`   | Vue components                        | Class-based CRM Form Scripts (in DB)      |
| DocType prefix       | None                             | `HD`                                  | `CRM`                                     |
| CSS approach         | Frappe Desk built-in             | Tailwind (semantic gray classes)      | Tailwind (frappe-ui preset)               |
| Icons                | Frappe built-in                  | Lucide (unplugin-icons)               | Lucide Vue Next + custom SVGs             |
| TypeScript           | No                               | Yes (`<script setup lang="ts">`)      | No (Composition API JS)                   |
| Frappe version req   | ≥15.x                           | ≥16.0.0-dev                           | ≥17.0.0-dev                               |

---

## Dependency Management

The bench environment uses a **managed virtual environment** at `frappe-bench/env/`. All apps share this single venv.

### Python Dependencies (v15+ uses pyproject.toml ONLY)

```toml
# pyproject.toml
[project]
name = "my_app"
authors = [{name = "Dev", email = "dev@example.com"}]
description = "My Custom App"
requires-python = ">=3.11"
dynamic = ["version"]
dependencies = [
    "requests~=2.31.0",
    "pdfkit~=1.0.0",
]

[build-system]
requires = ["flit_core >=3.4,<4"]
build-backend = "flit_core.buildapi"

[tool.bench.frappe-dependencies]
frappe = ">=15.0.0,<16.0.0"
```

**Never list Frappe apps** (frappe, erpnext) in the `dependencies` array — they are not on PyPI. Use `[tool.bench.frappe-dependencies]` instead.

### What NEVER to Do

- **`pip install package`** — installs in wrong environment. Use `bench pip install` for testing, then add to `pyproject.toml`
- **`sudo pip install` anything** — corrupts system Python
- **`npm install` at bench root** — bench uses Yarn
- **`setup.py` for new apps on v15+** — use `pyproject.toml` only
- **Hardcode hashed asset paths** — use `bundled_asset()` or `.bundle.js` naming

### What to ALWAYS Do

- Declare Python deps in `pyproject.toml` under `dependencies`
- Declare Frappe app deps under `[tool.bench.frappe-dependencies]`
- Declare required apps in `hooks.py`: `required_apps = ["frappe"]`
- Use `bench setup requirements` after changing dependency files
- Use `bench build --app my_app` after changing JS/CSS
- Name bundle entry points with `.bundle.js` / `.bundle.css` suffix

### Recovery Commands

```bash
bench setup env                    # Recreate Python venv
bench setup requirements           # Reinstall all deps
bench setup requirements --python  # Python only
bench setup requirements --node    # Node only
bench build                        # Rebuild all assets
bench --site sitename migrate      # Apply schema changes + patches
bench migrate-env python3.14       # Migrate to new Python version
```

---

## Breaking Changes — v14 → v15 → v16

### Python APIs Removed or Renamed in v15

| Old (BROKEN) | New (v15+) |
|---|---|
| `frappe.db.set(doctype, name, field, val)` | `doc.db_set(field, val)` |
| `frappe.db.set_value("Single", None, field, val)` | `frappe.db.set_single_value("Single", field, val)` |
| `frappe.cache().get_value()` | `frappe.cache.get_value()` (property, not method) |
| `frappe.compare(a, op, b)` | `from frappe.utils import compare` |
| `frappe.db.clear_table()` | `frappe.db.truncate()` |
| `frappe.db.update()` | `frappe.db.set_value()` |
| `frappe.utils.get_site_url()` | `frappe.utils.get_url()` |
| `frappe.enqueue(..., job_name=x)` | `frappe.enqueue(..., job_id=x)` |

### JavaScript Globals Removed in v15

| Old (BROKEN) | New (v15+) |
|---|---|
| `get_today` | `frappe.datetime.get_today()` |
| `user` | `frappe.session.user` |
| `user_fullname` | `frappe.session.user_fullname` |
| `user_email` | `frappe.session.user_email` |
| `validated` | `frappe.validated` |
| `show_alert(msg)` | `frappe.show_alert(msg)` |
| `user_defaults` | `frappe.user_defaults` |
| `roles` | `frappe.user_roles` |
| `sys_defaults` | `frappe.sys_defaults` |

### Critical v16 Changes

- **Default sort order changed**: All `frappe.get_all`, `frappe.get_list`, `frappe.db.get_value` now sort by **`creation desc`** instead of `modified desc`.
- **`frappe.get_all()` fields no longer accept raw SQL** — use dict syntax or Pypika.
- **`frappe.db.get_value()` returns typed values for Single DocTypes**: `"1"` (string) → `1` (int).
- **`has_permission` hooks must return `True` explicitly** — returning `None` no longer means "allowed."
- **Report/Page/Dashboard Chart JS loaded as IIFEs** — variables no longer pollute global scope.
- **State-changing methods require POST**: `/api/method/logout`, `/api/method/upload_file`, etc. reject GET.
- **`frappe.flags.in_test`** deprecated — use `frappe.in_test`.
- **Modules separated from core**: Newsletter, Blog, Energy Points → separate apps. Google Drive/S3 backup → `offsite_backups` app.
- **Server scripts disabled by default in v15+**: Enable with `bench set-config -g server_script_enabled 1`.
- **Vue 2 → Vue 3**: Any custom Vue code must use Vue 3 from v15 onward.
- **`setup.py` removed**: v15+ uses `pyproject.toml` only with `flit_core` as build backend.
- **`build.json` deprecated since v14**: Use `*.bundle.js` / `*.bundle.css` file naming convention.

---

## Testing and Debugging

### Writing Tests

```python
import frappe
from frappe.tests.utils import FrappeTestCase

class TestMyDoctype(FrappeTestCase):
    def test_creation(self):
        doc = frappe.get_doc({"doctype": "My DocType", "title": "Test"}).insert()
        self.assertEqual(doc.status, "Open")
        doc.delete()
```

**Always inherit from `FrappeTestCase`**, not raw `unittest.TestCase`. Test files must be named `test_*.py` and run on a site whose name starts with `test_`.

### Running Tests

```bash
bench --site test_site run-tests --app my_app
bench --site test_site run-tests --doctype "My DocType"
bench --site test_site run-tests --doctype "My DocType" --test test_creation
```

### Interactive Debugging

```bash
bench --site mysite console           # IPython with Frappe loaded
bench --site mysite mariadb           # Direct database access
bench --site mysite execute frappe.db.get_database_size  # One-off method call
```

### Log Files and Error Tracking

- **Error Log DocType** at `/app/error-log` — all server errors, background job failures
- **Log files**: `logs/web.log`, `logs/worker.log`, `logs/web.err.log`, `logs/worker.err.log`
- **`frappe.log_error(title="My Error", message=frappe.get_traceback())`** — programmatic logging
- **System Console** at `/app/system-console` — in-browser Python REPL
- **`bench doctor`** — background job status

### Developer Mode

```bash
bench set-config -g developer_mode 1  # Enable
# Enables: DocType editing via UI, auto-reload, detailed tracebacks
# NEVER enable on production systems
```

### Recovering from Broken Migrations

```bash
bench --site mysite migrate --verbose          # See what's failing
bench --site mysite restore path/to/backup.sql.gz  # Restore backup
bench --site mysite --force reinstall          # Nuclear option (wipes DB)
```

---

## Advanced Technical Reference

### 1. Patches (Data Migrations)

**File location:** `<app_root>/<app_name>/patches.txt`

**Format — two-section INI style (v14+):**
```ini
[pre_model_sync]
myapp.patches.v15_0.fix_old_field_data
myapp.patches.v15_0.migrate_legacy_records

[post_model_sync]
myapp.patches.v15_0.populate_new_field
myapp.patches.v15_0.set_default_values
```

`[pre_model_sync]` patches run **before** DocType schema sync; `[post_model_sync]` patches run **after**. Without section headers, all patches are treated as pre_model_sync. Inline execution: `execute:frappe.db.set_default("key", "value")`.

**Patch function — exact required signature:**
```python
import frappe

def execute():
    # patch code here — NO parameters
    pass
```

In `[pre_model_sync]` patches, call `frappe.reload_doc(module, "doctype", doctype_name)` to access new schema. In `[post_model_sync]` patches, all DocTypes are already reloaded.

**Tracking:** Executed patches are recorded in `tabPatch Log`. To re-run a patch, append a comment: `myapp.patches.v15_0.my_patch #2024-03-22`.

**`bench migrate` flow:**
1. Run `before_migrate` hooks
2. Run `[pre_model_sync]` patches
3. Sync DocType schemas from JSON to database
4. Run `[post_model_sync]` patches
5. Sync fixtures, dashboards, workspaces
6. Run `after_migrate` hooks
7. Clear all caches

**Commands:**
```bash
bench --site sitename migrate --skip-failing     # Skip failing patches
bench --site sitename run-patch myapp.patches.v15_0.my_patch  # Run single patch
```

**Hooks:**
```python
before_migrate = ["myapp.utils.before_migrate_handler"]
after_migrate = ["myapp.utils.after_migrate_handler"]
```

### 2. Error Handling Patterns

**`frappe.throw()`** — full signature:
```python
def throw(
    msg: str,
    exc: type[Exception] = ValidationError,
    title: str | None = None,
    is_minimizable: bool = False,
    wide: bool = False,
    as_list: bool = False,
    primary_action=None,  # v16
) -> None
```
Always raises an exception. Use for validation errors that must halt execution.

**`frappe.msgprint()`** — full signature:
```python
def msgprint(
    msg: str,
    title: str | None = None,
    raise_exception: bool | type[Exception] = False,
    as_table: bool = False,
    as_list: bool = False,
    indicator: Literal["blue", "green", "orange", "red", "yellow"] | None = None,
    alert: bool = False,
    primary_action: str | None = None,
    is_minimizable: bool = False,
    wide: bool = False,
) -> None
```
With `alert=True`, shows a dismissible toast instead of modal.

**`frappe.log_error()`** — v14+ signature (breaking change from v13):
```python
def log_error(title=None, message=None, reference_doctype=None, reference_name=None)
```
Creates an Error Log document. If `message` is omitted, current traceback is auto-captured. **Old pattern (broken):** `frappe.log_error(frappe.get_traceback(), "Title")` — arguments were swapped in v14.

**Exception classes:**

| Exception | HTTP Status |
|-----------|-------------|
| `frappe.ValidationError` | 417 |
| `frappe.AuthenticationError` | 401 |
| `frappe.PermissionError` | 403 |
| `frappe.DoesNotExistError` | 404 |
| `frappe.DuplicateEntryError` | 409 |
| `frappe.MandatoryError` | 417 |
| `frappe.TimestampMismatchError` | 417 |
| `frappe.TooManyRequestsError` | 429 |

**When to use each:**
- `frappe.throw(msg, exc)` — Stop execution AND notify user. Always raises.
- `frappe.msgprint(msg)` — Notify user WITHOUT stopping execution.
- `frappe.log_error(title)` — Silent server-side logging.

**Common mistake:** Using `raise frappe.ValidationError("msg")` directly instead of `frappe.throw("msg")` — skips message_log so users see no dialog.

### 3. Email Sending

**`frappe.sendmail()`** — key parameters:
```python
frappe.sendmail(
    recipients=None, sender="", subject="No Subject", message="No Message",
    as_markdown=False, delayed=True, reference_doctype=None, reference_name=None,
    attachments=None, cc=None, bcc=None, reply_to=None,
    template=None, args=None, header=None, now=None,
    send_priority=1, queue_separately=False,
)
```

- `delayed=True` queues via Email Queue (default); `now=True` sends immediately
- `template` names a Jinja template in `templates/emails/` or an Email Template DocType
- `args` is a dict passed to the template for rendering
- `attachments` is a list of dicts with `fname` and `fcontent` keys, or output from `frappe.attach_print()`

**Critical rule:** Never use `smtplib` directly. `frappe.sendmail()` is the correct API. `frappe.send_mail()` does NOT exist as a public API.

### 4. File and Attachment Handling

**File URL patterns:**
- Public: `/files/<filename>` → stored at `<site>/public/files/`
- Private: `/private/files/<filename>` → stored at `<site>/private/files/` (requires authentication)

**Recommended programmatic attachment:**
```python
_file = frappe.get_doc({
    "doctype": "File",
    "file_name": "report.pdf",
    "content": file_content_bytes,
    "attached_to_doctype": "Sales Invoice",
    "attached_to_name": "SINV-00001",
    "folder": "Home/Attachments",
    "is_private": 1,
})
_file.save()
```

**Upload endpoint:** `POST /api/method/upload_file` with `multipart/form-data`.

**`frappe.attach_print()`** — for email attachments:
```python
def attach_print(doctype, name, file_name=None, print_format=None,
    style=None, html=None, doc=None, lang=None, print_letterhead=True)
# Returns: {"fname": "...", "fcontent": <bytes>}
```

### 5. Realtime/Socket Events

**`frappe.publish_realtime()`** — exact signature:
```python
def publish_realtime(
    event: str = None,
    message: dict = None,
    room: str = None,
    user: str = None,
    doctype: str = None,
    docname: str = None,
    task_id: str = None,
    after_commit: bool = False,
)
```

**`after_commit=True` is critical** for data-change notifications — events are buffered and only emitted after DB transaction commits.

**Room format strings:** `"user:{user}"`, `"doctype:{doctype}"`, `"doc:{doctype}/{docname}"`, `"task_progress:{task_id}"`, `"all"`.

**`frappe.publish_progress()`**:
```python
def publish_progress(percent, title=None, doctype=None, docname=None, description=None, task_id=None)
```

**Client-side:**
```javascript
frappe.realtime.on('event_name', (data) => { /* handle */ });
frappe.realtime.off('event_name');
```

### 6. Translation/i18n

**Python:** `_()`
```python
from frappe import _
msg = _("Document submitted successfully")
_("Hello {0}").format(name)  # CORRECT
_(f"Hello {name}")           # WRONG — f-strings break extraction
_("Submit", context="Submit a DocType")  # with context
```

**JavaScript:** `__()`
```javascript
__('Hello {0}, you have {1} items', [user_name, count])
__('Change', null, 'Coins')  // with context
```

**Translation CSV files:** `<app>/<app_name>/translations/<lang_code>.csv` — format: `"source","translated","context"`

**Language resolution:** `_lang` URL param → `preferred_language` cookie → `Accept-Language` header → User `language` field → System Settings `language`.

### 7. Print Formats

**Types:** Standard (auto-generated), Custom Jinja (HTML in `html` field), Print Format Builder (drag-and-drop).

**Jinja template context:** `doc`, `meta`, `frappe`, `print_settings`, `letter_head`, `no_letterhead`, `nowdate`, `nowtime`, `_`.

**PDF generation:**
```python
# Whitelisted endpoint:
frappe.utils.print_format.download_pdf(doctype, name, format=None, no_letterhead=0)
# REST: GET /api/method/frappe.utils.print_format.download_pdf?doctype=X&name=Y&format=Z

# HTML to PDF:
frappe.utils.pdf.get_pdf(html, options=None)

# For email attachments:
frappe.attach_print(doctype, name, print_format="My Format")
```

### 8. Script Reports

**`execute()`** — required function signature:
```python
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data
    # Full return: (columns, data, message, chart, report_summary, skip_total_row)
```

**Column format (dict):**
```python
{"fieldname": "account", "label": _("Account"), "fieldtype": "Link", "width": 200, "options": "Account"}
```

**Report JS (filters):**
```javascript
frappe.query_reports['My Report'] = {
    filters: [
        { fieldname: 'company', label: __('Company'), fieldtype: 'Link',
          options: 'Company', default: frappe.defaults.get_user_default('company'), reqd: 1 },
    ],
};
```

**Chart return format:**
```python
chart = {
    "data": {"labels": ["Jan", "Feb"], "datasets": [{"values": [23, 45], "name": "Revenue"}]},
    "type": "bar",  # "bar", "line", "pie", "percentage", "axis-mixed"
}
```

**Report summary:**
```python
[{"value": profit, "indicator": "Green", "label": _("Total Profit"), "datatype": "Currency", "currency": "USD"}]
```

**File structure:** `<app>/<module>/report/<report_name>/__init__.py, .py, .js, .json`

### 9. Workflows

**Workflow DocType key fields:** `document_type`, `is_active` (only one active per DocType), `workflow_state_field` (default: `"workflow_state"`), `states` (child table), `transitions` (child table).

**Workflow Transition:** `state` (source), `action`, `next_state` (target), `allowed` (Role), `allow_self_approval`, `condition` (Python expression via `frappe.safe_eval`).

**`apply_workflow()`:**
```python
from frappe.model.workflow import apply_workflow
apply_workflow(doc, action)
```

**Docstatus interaction:**
- `0 → 0`: `doc.save()` (state change within Draft)
- `0 → 1`: `doc.submit()`
- `1 → 1`: `doc.save()` (state change within Submitted)
- `1 → 2`: `doc.cancel()`

The `workflow_state` field is auto-created as a Custom Field when a workflow is activated.

### 10. Virtual DocTypes (v15+)

Set `"is_virtual": 1` in the DocType JSON. No database table is created.

**Required controller methods:**
```python
class MyVirtualDoc(Document):
    @staticmethod
    def get_list(args):
        """Return list of dicts, each with 'name' key"""

    @staticmethod
    def get_count(args):
        """Return integer count"""

    def db_insert(self, *args, **kwargs):
        """Replaces DB INSERT"""

    def load_from_db(self):
        """Replaces DB SELECT — must call super(Document, self).__init__(data_dict)"""

    def db_update(self, *args, **kwargs):
        """Replaces DB UPDATE"""

    def delete(self):
        """Replaces DB DELETE"""
```

**Use cases:** External API wrappers, secondary databases, JSON/CSV-backed data, computed views.

### 11. Custom Fields vs Property Setters

**Custom Field:** Adds a new field to an existing DocType. Named `{DocType}-{fieldname}`. Lives in `tabCustom Field` (database), NOT in DocType JSON. **Survives app updates.**

**Property Setter:** Modifies properties of existing fields (e.g., making a field hidden or mandatory). Lives in `tabProperty Setter`.

**Programmatic creation:**
```python
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
create_custom_fields({
    "Sales Invoice": [
        {"fieldname": "custom_gstin", "label": "GSTIN", "fieldtype": "Data", "insert_after": "company"}
    ]
})
```

**Fixtures in hooks.py:**
```python
fixtures = [
    {"dt": "Custom Field", "filters": [["name", "in", ["Sales Invoice-custom_field1"]]]},
    {"dt": "Property Setter", "filters": [["doc_type", "=", "Sales Invoice"]]},
]
```

### 12. Site Configuration

**`site_config.json`** — `frappe-bench/sites/{sitename}/site_config.json`. Essential keys: `db_name`, `db_password`, `db_type`, `admin_password`, `encryption_key`. Common keys: `developer_mode`, `mute_emails`, `maintenance_mode`, `pause_scheduler`, `server_script_enabled`.

**`common_site_config.json`** — shared by all sites. Contains Redis, port, worker config. Site config overrides common config.

**`frappe.conf` API:**
```python
db_name = frappe.conf.db_name
api_key = frappe.conf.get("my_api_key")
```

**Storing secrets:**
- Option 1: Put in `site_config.json`, access via `frappe.conf.get("my_secret")`
- Option 2: Use a Settings Single DocType with Password fieldtype, retrieve via `frappe.utils.password.get_decrypted_password("My Settings", "My Settings", "api_secret")`

### 13. Advanced Permission Patterns

**`frappe.has_permission()`:**
```python
frappe.has_permission(doctype, ptype="read", doc=None, user=None, throw=False)
```

**User Permissions** (row-level): Restrict which records a user can see based on Link field values. They **restrict**, not grant.

**Permission Level** (field-level): Each field has `permlevel` (0, 1, 2...). Different roles get read/write on different permlevels.

**`frappe.only_for(roles)`** — not a decorator, called inline:
```python
frappe.only_for("Script Manager", True)  # Raises PermissionError if user lacks role
```

**Permission query conditions:**
```python
# hooks.py
permission_query_conditions = {"Sales Invoice": "myapp.permissions.get_conditions"}
# Function returns SQL WHERE clause:
def get_conditions(user):
    if user == "Administrator": return ""
    return f"`tabSales Invoice`.owner = {frappe.db.escape(user)}"
```

**`has_permission` hook:** Return `None` to defer to standard checks. Only `False` explicitly denies. In v16, must return `True` explicitly to allow.

**`ignore_permissions` flag:**
```python
frappe.get_list("DocType", ignore_permissions=True)
doc.insert(ignore_permissions=True)
doc.flags.ignore_permissions = True; doc.save()
```
Note: `frappe.get_all()` is `frappe.get_list()` with `ignore_permissions=True` as default.

### 14. Bench Multisite Architecture

**Site resolution:** Production: Nginx `Host` header → `sites/{hostname}/` directory. Development: falls back to `currentsite.txt`.

```bash
bench new-site sitename [--db-type mariadb|postgres] [--admin-password X] [--install-app erpnext]
bench use sitename              # Sets currentsite.txt
bench --site all migrate        # All sites
bench setup nginx               # Generate nginx config for multitenancy
```

### 15. Frappe Utility Functions

**Import:** `from frappe.utils import <function>`

**Date/time:**
```python
now() -> str           # "YYYY-MM-DD HH:MM:SS.ffffff"
nowdate() -> str       # "YYYY-MM-DD"
today() -> str         # Alias for nowdate()
add_days(date, days), add_months(date, months), add_years(date, years)
date_diff(date1, date2) -> int
getdate(string_date) -> datetime.date
get_datetime(string) -> datetime.datetime
```

**Type conversion:**
```python
flt(s, precision=None) -> float   # Returns 0.0 on failure
cint(s, default=0) -> int         # Returns 0 on failure
cstr(s) -> str
```

**Formatting:**
```python
fmt_money(amount, precision=None, currency=None) -> str
money_in_words(number, main_currency=None) -> str
```

**Random/hash:**
```python
random_string(length) -> str
frappe.generate_hash(txt=None, length=56) -> str  # On frappe, NOT frappe.utils
```

**HTML/string:**
```python
strip_html(html_text) -> str
sanitize_html(html) -> str  # from frappe.utils.html_utils
comma_and(some_list) -> str  # '"a", "b" and "c"'
unique(seq) -> list          # Deduplicate preserving order
```

**Common mistakes:** Importing `generate_hash` from `frappe.utils` (it's on `frappe` itself). Confusing `nowdate()` (string) with `getdate()` (date object).

### 16. Dashboard Charts and Number Cards

**Dashboard Chart types:** Count, Sum, Average, Group By, Custom, Report.

**Custom chart source:**
```python
@frappe.whitelist()
def get_chart_data(filters=None):
    return {
        "labels": ["Jan", "Feb", "Mar"],
        "datasets": [{"values": [23, 45, 56], "name": "Revenue"}],
        "type": "bar",
    }
```

**Number Card types:** Document Type, Report, Custom. Custom method must return: `{"value": 50, "fieldtype": "Currency"}`.

### 17. Workspace Customization (v15/v16)

**Key fields:** `title`, `module`, `public` (1=sidebar, 0=MY WORKSPACES), `for_user`, `parent_page`, `content` (JSON-encoded block layout), `roles` (child table).

**Block types:** `"header"`, `"shortcut"`, `"card"`, `"chart"`, `"number_card"`, `"custom_block"`, `"spacer"`, `"text"`, `"onboarding"`.

**Fixture export:**
```python
fixtures = [{"dt": "Workspace", "filters": [["module", "=", "My Module"]]}]
```

### 18. Data Import

**CSV format:** Headers use field labels or fieldnames. Date format: `YYYY-MM-DD`. Link fields use `name` value. Check fields: `0`/`1`.

**Child table format:**
```csv
ID,Customer,Posting Date,items:item_code,items:qty,items:rate
,CUST-001,2024-01-15,ITEM-A,10,100
,,,ITEM-B,5,200
```

**CLI:** `bench --site <site> data-import --file /path.csv --doctype Customer --type Insert`

**Programmatic:**
```python
from frappe.core.doctype.data_import.importer import Importer
i = Importer(doctype="Customer", data_import=data_import_doc, file_path="/path.csv")
i.import_data()
```

### 19. Webhooks

**Key fields:** `webhook_doctype`, `webhook_docevent`, `condition` (Python expression), `request_url`, `request_method` (POST/PUT/DELETE), `request_structure` (""/Form URL-Encoded/JSON), `webhook_json` (Jinja template), `enable_security`, `webhook_secret`.

**Supported events:** `after_insert`, `on_update`, `on_submit`, `on_cancel`, `on_trash`, `on_update_after_submit`, `on_change`.

**Secret verification:** Adds `X-Frappe-Webhook-Signature` header containing base64-encoded HMAC-SHA256 hash of JSON payload.

**Execution:** Webhooks are fired **after DB commit**, then executed as **background jobs**. Results logged in **Webhook Request Log**.

**Condition field:**
```python
doc.status == "Approved"
doc.grand_total > 10000
```

### 20. Document Naming Series

**Format tokens:** `.YYYY.`/`{YYYY}` (4-digit year), `.YY.`/`{YY}`, `.MM.`/`{MM}`, `.DD.`/`{DD}`, `.#####`/`{#####}` (counter — number of `#` controls zero-padding), `{fieldname}` (document field value).

**Key functions from `frappe/model/naming.py`:**
```python
make_autoname(key="", doctype="", doc=None) -> str
getseries(key, digits, doctype="") -> str
revert_series_if_last(key, name, doc=None)
```

**Series tracking:** `tabSeries` table stores `name` (prefix key) and `current` (integer counter). Each call atomically increments using `SELECT ... FOR UPDATE`.

**Controller override:**
```python
class MyDoc(Document):
    def autoname(self):
        self.name = make_autoname(f"PRE-{self.category}-.#####", doc=self)
```

**`naming_series` field:** If a DocType has a Select field named `naming_series`, set `autoname = "naming_series:"`. Options define available patterns:
```
INV-.YYYY.-.#####
SINV-.YYYY.-.#####
```

**Document Naming Rule DocType:** Allows conditional naming rules per DocType with different series based on document field values.

**`name` constraints:** Unique per DocType. Max **140 characters** (VARCHAR(140)).

**Common mistakes:** Using `{YYYY}` inside `.` delimiters (use either `{YYYY}` in format strings OR `.YYYY.` in naming series, never both). Setting `autoname` in DocType JSON while also expecting `naming_series` to work without `naming_series:` prefix.

---

## AI Anti-Pattern Checklist

Every item below represents a documented, real-world AI coding failure with Frappe. Check generated code against every item:

1. **Never generate Flask/FastAPI patterns** — no `@app.route()`, no `Flask(__name__)`, no `uvicorn.run()`. Use `@frappe.whitelist()` and `/api/method/` and `/api/resource/`.
2. **Never generate Django patterns** — no `models.py`, no `views.py`, no `urls.py`, no `manage.py`. Use DocType JSON for models, controllers for logic, hooks.py for integration.
3. **Never generate standalone React/Vue apps for Desk features** — the Desk is jQuery-based. Use `frappe.ui.form.on()` and jQuery for Desk customization.
4. **Never invent bench CLI commands** — `bench new-doctype` does NOT exist. DocTypes are created via the Desk UI in developer mode.
5. **Never use `frappe.get_doc()` for simple lookups** — use `frappe.db.get_value()`.
6. **Never use `frappe.db.set_value()` for Single DocTypes** — use `frappe.db.set_single_value()`.
7. **Never use `frappe.cache()` with parentheses** — it's `frappe.cache` (property) since v15.
8. **Never use JavaScript window globals** like `get_today`, `user`, `validated` — use `frappe.*` namespaced equivalents.
9. **Never use raw SQL expressions in `frappe.get_all()` fields in v16** — use dict syntax or Pypika.
10. **Never assume `modified desc` sort order** — v16 defaults to `creation desc`.
11. **Never use `setup.py` or `requirements.txt` for v15+ apps** — use `pyproject.toml`.
12. **Never run `pip install` directly** — use `bench pip install` for testing, declare in `pyproject.toml`.
13. **Never generate `build.json`** — deprecated since v14. Use `*.bundle.js` file naming.
14. **Never assume server scripts are enabled** — disabled by default in v15+.
15. **Never use Vue 2 syntax** — must be Vue 3 from v15 onward.
16. **Never use string formatting in `frappe.db.sql()`** — always use parameterized queries with `%s`.
17. **Never create files outside the correct directory structure** — files in wrong locations are silently ignored.
18. **Never forget `frappe.db.commit()` in background jobs** — auto-commit only happens at request end.
19. **Never return `None` from `has_permission` hooks in v16** — must explicitly return `True`.
20. **Never use GET for state-changing API methods in v16** — use POST for logout, upload, etc.

---

## Checklist Before Creating Any Item

- [ ] Identified which app this belongs to (ERPNext / Helpdesk / CRM / custom)
- [ ] Using correct DocType naming prefix (none / HD / CRM)
- [ ] Creating in correct directory path
- [ ] Using correct frontend pattern for the target app
- [ ] Added hooks in `hooks.py` if extending existing DocTypes
- [ ] Will run `bench --site {site} migrate` after DocType changes
- [ ] Tests written in `test_*.py`
