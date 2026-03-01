# The definitive AI rules file for Frappe v15/v16 development

**Frappe Framework is a metadata-driven, full-stack Python web framework where AI coding tools consistently produce broken code because they confuse Frappe's unique patterns with Flask, Django, or React conventions.** This document eliminates every major category of AI-generated breakage — dependency conflicts, DocType schema errors, frontend failures, and API routing bugs — by encoding the exact patterns, APIs, and file structures that Frappe v15 and v16 actually use. Community evidence from the Frappe Forum, the Lubus agency's "Frappe Skills for AI Agents" project, and hundreds of developer reports confirms that AI tools hallucinate non-existent Frappe commands, mix in patterns from other frameworks, use deprecated APIs, and generate code that "works but doesn't fit." What follows is the authoritative reference to prevent all of this.

---

## How Frappe's architecture differs from what AI assumes

Frappe is **not** Flask, Django, FastAPI, or any conventional MVC framework. It is a **metadata-driven** full-stack framework where the DocType (a JSON schema definition) simultaneously defines the database table, the ORM model, the REST API, the form UI, the list view, permissions, and search behavior. AI tools must understand that **declarative configuration replaces imperative code** for most tasks.

**Core technology stack**: Python 3.11+ (v15) or **Python 3.14+** (v16), MariaDB/PostgreSQL (v16 adds SQLite), Redis, Node.js 18+ (v15) or **Node.js 24+** (v16), Socket.IO for realtime, RQ (Redis Queue) for background jobs, Jinja2 for templates, esbuild for asset bundling, jQuery + Bootstrap 4 for the Desk UI.

**Key architectural truths AI must internalize**:

- **Everything is a DocType.** Users, roles, permissions, settings, error logs, scheduled jobs — all DocTypes. There is no separate ORM layer, no models.py, no migrations directory. The DocType JSON *is* the schema.
- **The bench CLI manages everything.** There is no `manage.py`, no `flask run`, no standalone `pip install`. The `bench` tool manages sites, apps, virtual environments, process supervision, database operations, and builds.
- **Apps contain modules, modules contain DocTypes.** The directory hierarchy is rigid and enforced. Files in the wrong location are silently ignored.
- **The Desk (admin UI) is jQuery-based**, not React or Vue. "Frappe UI" is a separate Vue 3 component library used only by standalone apps like Frappe CRM, Insights, and Helpdesk — it does **not** power the main Desk.
- **Two routing domains exist**: the Desk SPA at `/app/*` (v15) or `/desk/*` (v16) for authenticated users, and the website/portal at root routes for public pages.

---

## Directory structure and file conventions

Running `bench new-app my_app` creates this exact structure:

```
apps/my_app/
├── my_app/
│   ├── __init__.py              # Contains __version__
│   ├── hooks.py                 # ALL integration points with Frappe core
│   ├── modules.txt              # Module names, one per line
│   ├── patches.txt              # Migration patches (dotted paths, run once in order)
│   ├── config/
│   │   ├── __init__.py
│   │   ├── desktop.py           # Module icon config
│   │   └── docs.py
│   ├── my_module/               # Module directory (matches entry in modules.txt)
│   │   ├── __init__.py
│   │   └── doctype/
│   │       └── my_doctype/
│   │           ├── __init__.py
│   │           ├── my_doctype.json    # DocType schema definition
│   │           ├── my_doctype.py      # Python controller
│   │           ├── my_doctype.js      # Client form script
│   │           ├── test_my_doctype.py # Unit tests
│   │           └── my_doctype_list.js # Optional list view customization
│   ├── public/                  # Static assets (served by nginx)
│   │   ├── js/
│   │   │   └── my_feature.bundle.js   # esbuild entry point
│   │   └── css/
│   │       └── my_style.bundle.scss
│   ├── templates/
│   │   └── includes/
│   └── www/                     # Portal pages (path = URL route)
├── pyproject.toml               # Python dependencies (v15+ ONLY format)
├── package.json                 # Node.js dependencies
├── license.txt
└── README.md
```

**Critical naming rules**: DocType directory names use **snake_case** matching the DocType's `name` lowercased with spaces replaced by underscores. The Python class name is **PascalCase**. The JSON file, Python file, and JS file all share the snake_case name. Getting any of these wrong causes silent failures.

---

## DocType JSON schema — the exact format

Every DocType is defined by a `.json` file. AI tools frequently generate incomplete or incorrectly structured schemas. Here is the complete structure:

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
  "engine": "InnoDB",
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

**All valid fieldtype values** (AI must only use these — never invent new ones):

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

**Auto-added columns** (always present, never in `fields` array): `name`, `creation`, `modified`, `modified_by`, `owner`, `docstatus` (0=Draft, 1=Submitted, 2=Cancelled), `idx`.

---

## Python controller patterns — the correct hooks

Controllers live at `{app}/{module}/doctype/{doctype_name}/{doctype_name}.py` and **must** extend `frappe.model.document.Document`:

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
        if not self.title:
            frappe.throw("Title is required")

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
        pass

    def before_cancel(self):
        """Before docstatus changes to 2"""
        pass

    def on_cancel(self):
        """After docstatus changes to 2"""
        pass

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

**Hook execution order**: Insert: `autoname` → `before_insert` → `before_validate` → `validate` → `before_save` → DB INSERT → `after_insert` → `on_update` → `on_change`. Update: `before_validate` → `validate` → `before_save` → DB UPDATE → `on_update` → `on_change`. Submit: `before_submit` → `on_submit` → `on_update` → `on_change`.

**Useful controller utilities**:
```python
old_doc = self.get_doc_before_save()   # Previous state in validate/on_update
self.has_value_changed("status")        # Check if field changed
self.is_new()                           # True only during insert flow
```

---

## Database and ORM API — every correct method

This is where AI tools fail most. **Never use SQLAlchemy, Django ORM, or raw DB connection patterns.** Use only these Frappe APIs:

### Document operations
```python
# Retrieve
doc = frappe.get_doc("Task", "TASK-001")          # Full document with child tables
doc = frappe.get_cached_doc("Company", "My Co")    # Cached for frequently-read docs

# Create
doc = frappe.new_doc("Task")
doc.title = "New Task"
doc.insert()                                        # Persists to DB

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

### Querying — use the right method for the job

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

**Filter syntax**:
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

**Other essential methods**:
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

**Critical anti-pattern**: AI tools overuse `frappe.get_doc()` for everything. **Do NOT** use `get_doc` just to read a single field value — it loads the entire document with all child tables. Use `frappe.db.get_value()` instead. Similarly, do NOT create a `get_doc` + `db_update` pattern when `frappe.db.set_value()` does it in one call.

**Table naming in raw SQL**: Always use backtick-quoted `tab` prefix: `` `tabSales Invoice` ``, `` `tabTask` ``. Never use bare table names.

---

## Query Builder (v16 critical changes)

In v16, **`frappe.get_all()` and `frappe.get_list()` internally use the Pypika-based Query Builder**, which breaks raw SQL expressions in fields:

```python
# ❌ BROKEN in v16:
frappe.get_all("Stock Ledger Entry", fields=["sum(actual_qty) as total"])

# ✅ CORRECT — dict-based syntax:
frappe.get_all("Stock Ledger Entry", fields=[{"SUM": "actual_qty", "as": "total"}])

# ✅ CORRECT — Pypika functions:
from frappe.query_builder.functions import Sum
sle = frappe.qb.DocType("Stock Ledger Entry")
frappe.get_all("Stock Ledger Entry", fields=[Sum(sle.actual_qty).as_("total")])
```

**Direct Query Builder usage**:
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

## Frontend and client script patterns

### The Desk is jQuery-based — not Vue, not React

The Frappe Desk (admin SPA at `/app/*` in v15, `/desk/*` in v16) uses **jQuery + Bootstrap 4 + a custom JavaScript framework**. It is NOT Vue or React. AI must never generate standalone React/Vue components for Desk customization.

**"Frappe UI"** is a separate Vue 3 + Tailwind CSS component library used ONLY by standalone apps (Frappe CRM, Insights, Builder, Helpdesk). It does NOT power the main Desk. To use Frappe UI in a custom app, scaffold a separate `frontend/` directory with Vue 3 via Doppio or `bench add-desk-page`.

### Form event hooks (client scripts)

```javascript
frappe.ui.form.on("My DocType", {
    setup(frm) {},                    // Once when form class instantiated
    onload(frm) {},                   // When form data loaded
    refresh(frm) {},                  // Every refresh (most commonly used)
    validate(frm) {},                 // Before save; return false to prevent
    before_save(frm) {},
    after_save(frm) {},
    before_submit(frm) {},
    on_submit(frm) {},
    before_cancel(frm) {},
    after_cancel(frm) {},

    // Field change events (fieldname as key):
    status(frm) {},
    customer(frm) {}
});

// Child table events:
frappe.ui.form.on("My Child Table", {
    item_code(frm, cdt, cdn) {
        let row = frappe.get_doc(cdt, cdn);
    },
    items_add(frm, cdt, cdn) {},
    items_remove(frm, cdt, cdn) {}
});
```

### Key `frm` methods
```javascript
frm.set_value("fieldname", value)                    // Returns Promise
frm.set_df_property("fieldname", "read_only", 1)
frm.toggle_display("fieldname", true)
frm.toggle_reqd("fieldname", true)
frm.add_custom_button("Label", callback, "Group")
frm.set_query("link_field", () => ({ filters: { status: "Active" } }))
frm.reload_doc()
frm.save()
frm.call({ method: "controller_method", args: {} })
frm.set_intro("Message", "blue")
frm.dashboard.add_indicator("Text", "green")
```

### JavaScript APIs for server calls
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

### List view customization

File: `{doctype_name}_list.js` in the DocType directory:
```javascript
frappe.listview_settings["My DocType"] = {
    add_fields: ["status", "priority"],
    filters: [["status", "=", "Open"]],
    hide_name_column: true,
    get_indicator(doc) {
        if (doc.status === "Open") return [__("Open"), "orange", "status,=,Open"];
        return [__("Closed"), "green", "status,=,Closed"];
    },
    formatters: {
        priority(value) { return value === "High" ? `<b>${value}</b>` : value; }
    }
};
```

---

## hooks.py — complete reference

### Asset injection
```python
app_include_js = ["my_feature.bundle.js"]        # Desk — use .bundle.js naming
app_include_css = ["my_style.bundle.css"]
web_include_js = ["my_web.bundle.js"]            # Website/portal
doctype_js = {"Sales Invoice": "public/js/sales_invoice.js"}
doctype_list_js = {"Sales Invoice": "public/js/sales_invoice_list.js"}
```

### Document events
```python
doc_events = {
    "Sales Invoice": {
        "validate": "my_app.events.si.validate",
        "on_submit": "my_app.events.si.on_submit",
        "on_cancel": "my_app.events.si.on_cancel",
    },
    "*": {  # All DocTypes
        "on_update": "my_app.events.all.on_update",
    }
}
# Handler signature: def handler(doc, method):
```

### Scheduler events
```python
scheduler_events = {
    "all": ["my_app.tasks.every_minute"],
    "hourly": ["my_app.tasks.hourly"],
    "daily": ["my_app.tasks.daily"],
    "weekly": ["my_app.tasks.weekly"],
    "monthly": ["my_app.tasks.monthly"],
    "cron": {
        "0 */6 * * *": ["my_app.tasks.every_six_hours"]
    }
}
```

### Permissions
```python
permission_query_conditions = {
    "Task": "my_app.permissions.task_conditions"
}
# def task_conditions(user): return "(`tabTask`.owner = '{user}')"

has_permission = {
    "Task": "my_app.permissions.task_permission"
}
# def task_permission(doc, ptype, user): return True  # MUST return True explicitly in v16
```

### Fixtures
```python
fixtures = [
    "Custom Field",
    {"doctype": "Property Setter", "filters": [["doc_type", "=", "Sales Invoice"]]},
    {"doctype": "Client Script", "filters": [["dt", "in", ["Task"]]]},
]
```
Export with `bench --site sitename export-fixtures`. Auto-imported on `bench migrate`.

### Other essential hooks
```python
required_apps = ["frappe"]
override_doctype_class = {"ToDo": "my_app.overrides.CustomToDo"}
override_whitelisted_methods = {"frappe.client.get_count": "my_app.overrides.custom_get_count"}
jinja = {"methods": ["my_app.jinja.custom_method"], "filters": ["my_app.jinja.custom_filter"]}
after_install = "my_app.setup.after_install"
before_uninstall = "my_app.setup.before_uninstall"
boot_session = "my_app.boot.boot_session"
website_route_rules = [{"from_route": "/custom/<path:app_path>", "to_route": "custom"}]
```

---

## API and routing patterns

### Whitelisted methods (RPC)
```python
@frappe.whitelist()
def get_customer_info(customer_name):
    """Accessible at /api/method/my_app.api.get_customer_info"""
    frappe.has_permission("Customer", throw=True)
    return frappe.db.get_value("Customer", customer_name, ["name", "territory"], as_dict=True)

@frappe.whitelist(allow_guest=True)
def public_endpoint():
    """No login required"""
    return {"status": "ok"}

@frappe.whitelist(methods=["POST"])
def create_record():
    """POST only"""
    data = frappe.form_dict   # All request parameters
    return {"received": data}
```

Parameters come through `frappe.form_dict`. Response wraps return value in `{"message": <value>}`.

### REST API (resource routes — built-in, no code needed)
```
GET    /api/resource/Customer?fields=["name","territory"]&filters=[["territory","=","US"]]&limit_page_length=20
GET    /api/resource/Customer/CUST-001
POST   /api/resource/Customer  (body: {"customer_name": "Acme"})
PUT    /api/resource/Customer/CUST-001  (body: {"territory": "UK"})
DELETE /api/resource/Customer/CUST-001
```

### Background jobs
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

---

## Dependency management — how to not break bench

The bench environment uses a **managed virtual environment** at `frappe-bench/env/`. All apps share this single venv.

### Python dependencies (v15+ uses pyproject.toml ONLY)
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

**Never list Frappe apps (frappe, erpnext) in the `dependencies` array** — they are not on PyPI. Use `[tool.bench.frappe-dependencies]` instead.

### Node.js dependencies
```json
{
  "name": "my_app",
  "version": "0.0.1",
  "private": true,
  "dependencies": { "dayjs": "^1.11.0" }
}
```
Then `bench setup requirements --node` and `bench build --app my_app`.

### What NEVER to do

- **`pip install package`** — installs in wrong environment. Use `bench pip install` for testing, then add to `pyproject.toml`
- **`sudo pip install` anything** — corrupts system Python
- **`npm install` at bench root** — bench uses Yarn
- **`setup.py` for new apps on v15+** — use `pyproject.toml` only
- **Hardcode hashed asset paths** — use `bundled_asset()` or `.bundle.js` naming

### What to ALWAYS do

- Declare Python deps in `pyproject.toml` under `dependencies`
- Declare Frappe app deps under `[tool.bench.frappe-dependencies]`
- Declare required apps in `hooks.py`: `required_apps = ["frappe"]`
- Use `bench setup requirements` after changing dependency files
- Use `bench build --app my_app` after changing JS/CSS
- Name bundle entry points with `.bundle.js` / `.bundle.css` suffix

### Recovery commands
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

## Every breaking change AI tools get wrong (v14→v15→v16)

### APIs removed or renamed in v15

| Old (BROKEN) | New (v15+) | Notes |
|---|---|---|
| `frappe.db.set(doctype, name, field, val)` | `doc.db_set(field, val)` | Completely removed |
| `frappe.db.set_value("Single", None, field, val)` | `frappe.db.set_single_value("Single", field, val)` | For Single DocTypes |
| `frappe.cache().get_value()` | `frappe.cache.get_value()` | Property, not method |
| `frappe.compare(a, op, b)` | `from frappe.utils import compare` | Moved out of frappe namespace |
| `frappe.db.clear_table()` | `frappe.db.truncate()` | Renamed |
| `frappe.db.update()` | `frappe.db.set_value()` | Renamed |
| `frappe.utils.get_site_url()` | `frappe.utils.get_url()` | Merged |
| `frappe.enqueue(..., job_name=x)` | `frappe.enqueue(..., job_id=x)` | Renamed parameter |
| `frappe.local.rollback_observers` | DB transaction hooks | Completely removed |

### JavaScript globals removed in v15

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
| `r.results` (search_link callback) | `r.message` |

### Critical v16 changes

**Default sort order changed**: All `frappe.get_all`, `frappe.get_list`, `frappe.db.get_value` now sort by **`creation desc`** instead of `modified desc`. Any code relying on "most recently modified first" without explicit `order_by` will behave differently.

**`frappe.get_all()` fields no longer accept raw SQL** — use dict syntax or Pypika (see Query Builder section above).

**`frappe.db.get_value()` now returns typed values for Single DocTypes**: where `"1"` (string) was returned before, now `1` (int) is returned. Check comparisons.

**`has_permission` hooks must return `True` explicitly** — returning `None` no longer means "allowed."

**Report/Page/Dashboard Chart JS now loaded as IIFEs** — variables no longer pollute global scope. Use `window.myVar` for intentional globals.

**State-changing methods require POST**: `/api/method/logout`, `/api/method/upload_file`, and others now reject GET requests.

**`frappe.flags.in_test`** deprecated in v16. Use `frappe.in_test`.

**Modules separated from core in v16**: Newsletter, Blog, Energy Points → separate apps. Google Drive/S3 backup → `offsite_backups` app. Must install separately.

**Server scripts disabled by default in v15+**: Enable with `bench set-config -g server_script_enabled 1`.

**Vue 2 → Vue 3**: Any custom Vue code must use Vue 3, Vuex 4, Vue Router 4 from v15 onward.

**`setup.py` removed**: v15+ uses `pyproject.toml` only with `flit_core` as build backend.

**`build.json` deprecated since v14**: Use `*.bundle.js` / `*.bundle.css` file naming convention instead.

**`frappe.new_doc()` argument change**: Positional args no longer work. Use keyword args: `frappe.new_doc("ToDo", description="test")`.

---

## Testing and debugging

### Writing tests
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

### Running tests
```bash
bench --site test_site run-tests --app my_app
bench --site test_site run-tests --doctype "My DocType"
bench --site test_site run-tests --doctype "My DocType" --test test_creation
```

### Interactive debugging
```bash
bench --site mysite console           # IPython with Frappe loaded
bench --site mysite mariadb           # Direct database access
bench --site mysite execute frappe.db.get_database_size  # One-off method call
```

### Log files and error tracking
- **Error Log DocType** at `/app/error-log` — all server errors, background job failures
- **Log files**: `logs/web.log`, `logs/worker.log`, `logs/web.err.log`, `logs/worker.err.log`
- **`frappe.log_error(title="My Error", message=frappe.get_traceback())`** — programmatic logging
- **System Console** at `/app/system-console` — in-browser Python REPL
- **`bench doctor`** — background job status

### Developer mode
```bash
bench set-config -g developer_mode 1  # Enable
# Enables: DocType editing via UI, auto-reload, detailed tracebacks
# NEVER enable on production systems
```

### Recovering from broken migrations
```bash
bench --site mysite migrate --verbose          # See what's failing
bench --site mysite restore path/to/backup.sql.gz  # Restore backup
bench --site mysite --force reinstall          # Nuclear option (wipes DB)
```

For stuck patches, insert into `tabPatch Log` to skip: `INSERT INTO \`tabPatch Log\` (name, patch) VALUES ('patch_name', 'patch_name');`

---

## The complete anti-pattern checklist for AI-generated code

Every item below represents a documented, real-world AI coding failure with Frappe. AI tools must check generated code against every item:

1. **Never generate Flask/FastAPI patterns** — no `@app.route()`, no `Flask(__name__)`, no `uvicorn.run()`. Frappe has its own routing via `@frappe.whitelist()` and `/api/method/` and `/api/resource/`.

2. **Never generate Django patterns** — no `models.py`, no `views.py`, no `urls.py`, no `manage.py`. Frappe uses DocType JSON for models, controllers for logic, and hooks.py for integration.

3. **Never generate standalone React/Vue apps for Desk features** — the Desk is jQuery-based. Use `frappe.ui.form.on()`, `frappe.listview_settings`, and jQuery for Desk customization.

4. **Never invent bench CLI commands** — `bench new-doctype` does NOT exist. DocTypes are created via the Desk UI in developer mode. The correct commands are `bench new-app`, `bench get-app`, `bench install-app`, `bench migrate`, `bench build`, `bench start`.

5. **Never use `frappe.get_doc()` for simple lookups** — use `frappe.db.get_value()` to fetch individual fields.

6. **Never use `frappe.db.set_value()` for Single DocTypes** — use `frappe.db.set_single_value()`.

7. **Never use `frappe.cache()` with parentheses** — it's `frappe.cache` (property) since v15.

8. **Never use JavaScript window globals** like `get_today`, `user`, `validated` — use their `frappe.*` namespaced equivalents.

9. **Never use raw SQL expressions in `frappe.get_all()` fields in v16** — use dict-based syntax or Pypika functions.

10. **Never assume `modified desc` sort order** — v16 defaults to `creation desc`.

11. **Never use `setup.py` or `requirements.txt` for v15+ apps** — use `pyproject.toml`.

12. **Never run `pip install` directly** — use `bench pip install` for testing, declare in `pyproject.toml` for permanent deps.

13. **Never generate `build.json`** — deprecated since v14. Use `*.bundle.js` file naming.

14. **Never assume server scripts are enabled** — disabled by default in v15+.

15. **Never use Vue 2 syntax** — must be Vue 3 from v15 onward.

16. **Never use string formatting in `frappe.db.sql()`** — always use parameterized queries with `%s` or `%(name)s`.

17. **Never create files outside the correct directory structure** — files in wrong locations are silently ignored.

18. **Never forget `frappe.db.commit()` in background jobs** — auto-commit only happens at request end, not in workers.

19. **Never return `None` from `has_permission` hooks in v16** — must explicitly return `True` to allow.

20. **Never use GET for state-changing API methods in v16** — use POST for logout, upload, and similar endpoints.

---

## Conclusion: using this document as a system prompt

This document should be provided as context to any AI coding tool before generating Frappe code. The most effective approach is to include the **version-specific sections** relevant to your target (v15 or v16), the **complete anti-pattern checklist**, and the **correct API reference sections** for whatever type of code you're generating. When asking AI to generate Frappe code, always specify: the exact Frappe version, whether ERPNext is installed, the target module path, and the existing DocType schema if modifying existing code. Treat all AI-generated Frappe code as coming from a talented developer who has never used Frappe — structurally competent but ignorant of every convention documented here. Verify every generated file path, every API call, every hook name, and every import statement against this reference before running the code.


# Frappe Framework v15/v16 technical reference for AI code generation

**This document provides exact API signatures, correct patterns, file paths, and common pitfalls for 20 critical Frappe Framework development topics.** Every signature below is verified against the `frappe/frappe` GitHub repository `develop` branch. AI coding tools frequently generate broken Frappe code by inventing non-existent APIs, using wrong parameter names, or applying patterns from other frameworks. This reference prevents those errors.

---

## 1. Patches (data migrations)

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

`[pre_model_sync]` patches run **before** DocType schema sync; `[post_model_sync]` patches run **after**. Without section headers, all patches are treated as pre_model_sync. Lines starting with `#` are comments. Blank lines are ignored. Inline execution is supported: `execute:frappe.db.set_default("key", "value")`.

**Patch function — exact required signature:**
```python
import frappe

def execute():
    # patch code here
    pass
```

The module **must** export a function named `execute` taking **no parameters**. File path convention: `myapp/patches/v<major>_<minor>/descriptive_name.py`. In `[pre_model_sync]` patches, call `frappe.reload_doc(module, "doctype", doctype_name)` to access new schema. In `[post_model_sync]` patches, all DocTypes are already reloaded.

**Tracking:** Executed patches are recorded in the **`tabPatch Log`** table (DocType: `Patch Log`). Before running a patch, the handler checks if the exact dotted path exists in Patch Log. To re-run a patch, append a comment to make the line unique: `myapp.patches.v15_0.my_patch #2024-03-22`.

**`bench migrate` flow (step by step):**
1. Verify Redis is running
2. Run `before_migrate` hooks from all apps
3. Run `[pre_model_sync]` patches from all apps
4. Sync all DocType schemas from JSON to database
5. Run `[post_model_sync]` patches from all apps
6. Sync fixtures, dashboards, workspaces, web pages
7. Build search index
8. Run `after_migrate` hooks from all apps
9. Clear all caches

**Skip failing patches:** `bench --site sitename migrate --skip-failing`. Failed patches are NOT recorded in Patch Log, so they retry on next migrate. Run a single patch manually: `bench --site sitename run-patch myapp.patches.v15_0.my_patch`.

**Hooks:**
```python
# hooks.py
before_migrate = ["myapp.utils.before_migrate_handler"]
after_migrate = ["myapp.utils.after_migrate_handler"]
```
Each referenced function takes no arguments.

**Common AI mistakes:** Giving `execute()` parameters like `filters` or `doc`. Using `frappe.get_doc().save()` in patches instead of the more efficient `frappe.db.set_value()`. Forgetting `frappe.reload_doc()` in pre_model_sync patches when accessing new fields.

---

## 2. Error handling patterns

### `frappe.throw()` — full signature (v15/v16)
```python
def throw(
    msg: str,
    exc: type[Exception] = ValidationError,
    title: str | None = None,
    is_minimizable: bool = False,
    wide: bool = False,
    as_list: bool = False,
    primary_action=None,  # v16 addition
) -> None
```
Internally calls `msgprint(msg, raise_exception=exc, title=title, indicator="red", ...)`. **Always raises an exception.** Use for validation errors that must halt execution.

### `frappe.msgprint()` — full signature
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
    *,
    realtime: bool = False,  # v16 keyword-only
) -> None
```
Messages are appended to `frappe.local.message_log`, serialized into the HTTP response as `__server_messages`, and displayed as modal dialogs client-side. With `alert=True`, shows a dismissible toast instead.

### `frappe.log_error()` — v14+ signature (breaking change from v13)
```python
def log_error(title=None, message=None, reference_doctype=None, reference_name=None, *, defer_insert=False)
```
Creates an **Error Log** document. If `message` is omitted, the current traceback is auto-captured. **Old pattern (broken):** `frappe.log_error(frappe.get_traceback(), "Title")` — arguments were swapped in v14.

### Exception classes (from `frappe/exceptions.py`)

| Exception | Base Class | HTTP Status |
|-----------|-----------|-------------|
| `frappe.ValidationError` | `Exception` | 417 |
| `frappe.AuthenticationError` | `Exception` | 401 |
| `frappe.PermissionError` | `Exception` | 403 |
| `frappe.DoesNotExistError` | `ValidationError` | 404 |
| `frappe.DuplicateEntryError` | `NameError` | 409 |
| `frappe.DataError` | `ValidationError` | 417 |
| `frappe.MandatoryError` | `ValidationError` | 417 |
| `frappe.TimestampMismatchError` | `ValidationError` | 417 |
| `frappe.OutgoingEmailError` | `Exception` | 501 |
| `frappe.TooManyRequestsError` | `Exception` | 429 |

All exceptions are importable from the `frappe` namespace (`from frappe.exceptions import *` is done in `frappe/__init__.py`).

**When to use each:**
- **`frappe.throw(msg, exc)`** — Stop execution AND notify user. Always raises. Use for validation failures.
- **`frappe.msgprint(msg)`** — Notify user WITHOUT stopping execution. Use for info/warnings.
- **`frappe.log_error(title)`** — Silent server-side logging. Use for background job errors or API failures the user shouldn't see immediately.

**Common AI mistakes:** Using `raise frappe.ValidationError("msg")` directly instead of `frappe.throw("msg")` — this skips the message_log mechanism so users see no dialog. Using the old `frappe.log_error(frappe.get_traceback(), "Title")` positional argument order.

---

## 3. Email sending

### `frappe.sendmail()` — full signature
```python
def sendmail(
    recipients=None, sender="", subject="No Subject", message="No Message",
    as_markdown=False, delayed=True, reference_doctype=None, reference_name=None,
    unsubscribe_method=None, unsubscribe_params=None, unsubscribe_message=None,
    add_unsubscribe_link=1, attachments=None, content=None, doctype=None, name=None,
    reply_to=None, queue_separately=False, cc=None, bcc=None, message_id=None,
    in_reply_to=None, send_after=None, expose_recipients=None, send_priority=1,
    communication=None, retry=1, now=None, read_receipt=None, is_notification=False,
    inline_images=None, template=None, args=None, header=None,
    print_letterhead=False, with_container=False,
)
```

Key parameters: **`delayed=True`** queues via Email Queue (default); **`now=True`** sends immediately. **`template`** names a Jinja template file in `templates/emails/` or an Email Template DocType. **`args`** is a dict passed to the template for rendering. **`attachments`** is a list of dicts with `fname` and `fcontent` keys, or output from `frappe.attach_print()`.

**Email Template DocType fields:** `name`, `subject` (Jinja-enabled), `response` (Jinja body), `use_html`, `response_html`.

**Notification DocType events:** `New`, `Save`, `Submit`, `Cancel`, `Days Before`, `Days After`, `Value Change`, `Method`, `Custom`. Days Before/After events run via the scheduler daily.

**Email Queue:** `frappe.sendmail()` with `delayed=True` creates an Email Queue document with status `"Not Sent"`. Background workers process the queue via `frappe.email.queue.flush()`.

**Critical rule: never use `smtplib` directly.** Frappe manages SMTP connections, OAuth tokens, retry logic, rate limits, audit trails (Communication records), and multi-tenancy through its Email Account system. Direct SMTP bypasses all of this.

**`frappe.sendmail()` is the correct API.** `frappe.send_mail()` does NOT exist as a public API — `send_mail` is an internal deprecated function.

---

## 4. File and attachment handling

### File DocType key fields
```python
file_name: DF.Data          # Original filename
file_url: DF.Code           # URL path (/files/x.pdf or /private/files/x.pdf)
is_private: DF.Check        # 0=public, 1=private
attached_to_doctype: DF.Link  # Parent DocType
attached_to_name: DF.Data     # Parent document name
attached_to_field: DF.Data    # Specific Attach field (optional)
folder: DF.Link             # Folder path (e.g., "Home/Attachments")
file_size: DF.Int
content_hash: DF.Data       # Deduplication hash
```

### `save_file()` — from `frappe/utils/file_manager.py`
```python
def save_file(fname, content, dt=None, dn=None, folder=None, decode=False, is_private=0, df=None)
```

### `save_url()`
```python
def save_url(file_url, filename, dt, dn, folder, is_private, df=None)
```

### `get_file()`
```python
def get_file(fname):
    """Returns [file_name, content] for given File document name"""
```

### File URL patterns
- **Public:** `/files/<filename>` → stored at `<site>/public/files/`
- **Private:** `/private/files/<filename>` → stored at `<site>/private/files/`  (requires authentication)

### Upload endpoint
`POST /api/method/upload_file` with `multipart/form-data`. Parameters: `file` (binary), `is_private`, `folder`, `doctype`, `docname`, `fieldname`.

### Recommended programmatic attachment pattern
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
The `file_url` is auto-generated on save. This is preferred over `save_file()` for clarity.

---

## 5. Realtime/socket events

### `frappe.publish_realtime()` — exact signature
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

**Room resolution order:** explicit `room` → `doctype:` room for `list_update` → `doc:` room for `docinfo_update` → `task_progress:` room if `task_id` → `user:` room if `user` → `doc:` room if `doctype`+`docname` → `"all"` (site broadcast).

**Room format strings:** `"user:{user}"`, `"doctype:{doctype}"`, `"doc:{doctype}/{docname}"`, `"task_progress:{task_id}"`, `"all"`.

**`after_commit=True` is critical** for data-change notifications. Events are buffered and only emitted after the DB transaction commits. On rollback, the buffer is cleared. Without it, clients may receive notifications about uncommitted data.

### `frappe.publish_progress()` — progress bar pattern
```python
def publish_progress(percent, title=None, doctype=None, docname=None, description=None, task_id=None)
```
The client automatically shows a progress dialog for `"progress"` events.

### Client-side API
```javascript
frappe.realtime.on('event_name', (data) => { /* handle */ });
frappe.realtime.off('event_name');
```

**Architecture:** Python → Redis pub/sub (`"events"` channel) → Node.js Socket.IO server → WebSocket → Browser. Each site gets its own Socket.IO namespace (`/{sitename}`).

---

## 6. Translation/i18n

### Python: `_()`
```python
from frappe import _
msg = _("Document submitted successfully")
_("Hello {0}").format(name)  # CORRECT
_(f"Hello {name}")           # WRONG — f-strings break extraction
_("Submit", context="Submit a DocType")  # with context
```
The string argument **must be a literal**, never a variable. Only `{0}`, `{1}` positional formatters work for extraction.

### JavaScript: `__()`
```javascript
__('Hello {0}, you have {1} items', [user_name, count])
__('Change', null, 'Coins')  // with context
// Signature: __('message', [format_args] | null, 'context')
```
Globally available in all client JS.

### Translation CSV files
**Location:** `<app>/<app_name>/translations/<lang_code>.csv`  
**Format:** `"source_string","translated_string","context"` (3-column CSV)

### Bench commands
```bash
bench --site <site> get-untranslated <lang> <output_path>
bench --site <site> update-translations <lang> <source> <translated>
```

**v15/v16 PO support:** Frappe is transitioning to gettext PO/MO files at `<app>/locale/<locale>/LC_MESSAGES/<app>.po`. CSV files still work.

**Language resolution priority:** `_lang` URL param → `preferred_language` cookie (guests only) → `Accept-Language` header → User `language` field → System Settings `language`.

**Pluralization:** Frappe has **no built-in plural forms**. Write separate complete strings for singular and plural cases.

---

## 7. Print formats

### Types
- **Standard:** Auto-generated from form layout, file-based in app
- **Custom (Jinja):** Check "Custom Format", write HTML/Jinja in the `html` field
- **Print Format Builder:** Drag-and-drop UI, client-side rendered (not Jinja)

### Jinja template context variables

| Variable | Description |
|----------|-------------|
| `doc` | Document being printed (all fields + child tables) |
| `meta` | DocType metadata |
| `frappe` | Frappe module (whitelisted methods) |
| `print_settings` | Print Settings document |
| `letter_head` | Letter Head content (`.content` header, `.footer` footer) |
| `no_letterhead` | Whether to suppress letter head |
| `nowdate` | `frappe.utils.nowdate` function |
| `nowtime` | `frappe.utils.nowtime` function |
| `_` | Translation function |

### PDF generation APIs

**`frappe.utils.print_format.download_pdf()`** — whitelisted endpoint:
```python
@frappe.whitelist()
def download_pdf(doctype, name, format=None, doc=None, no_letterhead=0, language=None, letterhead=None)
```
REST: `GET /api/method/frappe.utils.print_format.download_pdf?doctype=X&name=Y&format=Z`

**`frappe.utils.pdf.get_pdf(html, options=None, output=None)`** — converts HTML to PDF bytes (uses wkhtmltopdf or Chrome).

**`frappe.attach_print()`** — for email attachments:
```python
def attach_print(doctype, name, file_name=None, print_format=None,
    style=None, html=None, doc=None, lang=None, print_letterhead=True, password=None)
# Returns: {"fname": "...", "fcontent": <bytes>}
```

### Letter Head DocType key fields
`content` (header HTML, Jinja-enabled with `{{ doc }}`), `footer` (footer HTML), `image`, `source` ("Image"/"HTML"), `is_default`.

---

## 8. Script reports

### `execute()` — required function signature
```python
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data
    # Full return: (columns, data, message, chart, report_summary, skip_total_row)
```

### Column format (new-style dict)
```python
{
    "fieldname": "account",       # REQUIRED: maps to data keys
    "label": _("Account"),        # REQUIRED: display name
    "fieldtype": "Link",          # REQUIRED: Data, Link, Currency, Float, Int, Date, etc.
    "width": 200,                 # optional
    "options": "Account",         # for Link: target DocType; for Currency: currency field
    "disable_total": True,        # optional: exclude from total row
}
```

**Old-style string format:** `"Label:Fieldtype/Options:Width"` (e.g., `"Account:Link/Account:200"`)

### Report JS file (filters)
```javascript
frappe.query_reports['My Report'] = {
    filters: [
        { fieldname: 'company', label: __('Company'), fieldtype: 'Link',
          options: 'Company', default: frappe.defaults.get_user_default('company'), reqd: 1 },
    ],
};
```

### Report types

| Type | Code | Charts | Flexibility |
|------|------|--------|-------------|
| **Report Builder** | None (GUI) | No | Basic columns/filters/group-by |
| **Query Report** | SQL in `.sql` file | No | Raw SQL |
| **Script Report** | Python `.py` + JS `.js` | Yes | Full Python |

### Chart return format
```python
chart = {
    "data": {"labels": ["Jan", "Feb"], "datasets": [{"values": [23, 45], "name": "Revenue"}]},
    "type": "bar",  # "bar", "line", "pie", "percentage", "axis-mixed"
    "height": 300,
}
```

### `report_summary` format
```python
[{"value": profit, "indicator": "Green", "label": _("Total Profit"), "datatype": "Currency", "currency": "USD"}]
```

### File structure
```
<app>/<module>/report/<report_name>/
    __init__.py, <report_name>.py, <report_name>.js, <report_name>.json
```

**v15 note:** Custom script reports require `server_script_enabled = 1` in site config. Standard (file-based) reports are unaffected.

---

## 9. Workflows

### Workflow DocType key fields
`workflow_name`, `document_type` (Link to DocType), `is_active` (Check — only one active per DocType), `workflow_state_field` (default: `"workflow_state"`), `states` (child table), `transitions` (child table).

### Workflow Document State (states child table)
`state` (Link to Workflow State), `doc_status` (Select: 0/1/2), `update_field`, `update_value`, `allow_edit` (Role), `is_optional_state` (Check).

### Workflow State DocType
`workflow_state_name` (name), `style` (Primary/Success/Danger/Warning/Info/Inverse), `icon`.

### Workflow Transition (transitions child table)
`state` (source), `action` (Link to Workflow Action Master), `next_state` (target), `allowed` (Role), `allow_self_approval` (Check), `condition` (Python expression evaluated with `frappe.safe_eval`).

### `apply_workflow()` — exact signature
```python
# from frappe.model.workflow import apply_workflow
@frappe.whitelist()
def apply_workflow(doc, action):
    """Allow workflow action on the current doc"""
```
Internally loads the doc, finds matching transition, validates approval access, updates the workflow state field, and calls `doc.save()`, `doc.submit()`, or `doc.cancel()` based on docstatus changes.

### Docstatus interaction
- `0 → 0`: `doc.save()` (state change within Draft)
- `0 → 1`: `doc.submit()`
- `1 → 1`: `doc.save()` (state change within Submitted)
- `1 → 2`: `doc.cancel()`

**The `workflow_state` field** is auto-created as a Custom Field on the target DocType when a workflow is activated.

---

## 10. Virtual DocTypes (v15+)

### Creation
Set `"is_virtual": 1` in the DocType JSON. No database table is created. Can only be created in developer mode.

### Required controller methods

**For list view (static methods):**
```python
@staticmethod
def get_list(args):
    """Return list of dicts, each with 'name' key"""

@staticmethod
def get_count(args):
    """Return integer count"""
```

**For CRUD (instance methods):**
```python
def db_insert(self, *args, **kwargs):
    """Replaces DB INSERT"""

def load_from_db(self):
    """Replaces DB SELECT — must call super(Document, self).__init__(data_dict)"""

def db_update(self, *args, **kwargs):
    """Replaces DB UPDATE"""

def delete(self):
    """Replaces DB DELETE"""
```

**Use cases:** External API wrappers, secondary databases, JSON/CSV file-backed data, computed views.

**v16 change:** Non-virtual parents can now have virtual child tables (previously both had to match).

---

## 11. Custom Fields vs Property Setters

### Custom Field DocType key fields
`dt` (parent DocType), `fieldname`, `fieldtype`, `label`, `insert_after`, `options`, `reqd`, `default`, `fetch_from`, `is_virtual`.

**Naming:** `{DocType}-{fieldname}`, e.g., `Sales Invoice-custom_gstin`.

### Property Setter DocType
`doc_type`, `doctype_or_field` ("DocType"/"DocField"), `field_name`, `property`, `value`, `property_type`.

### Survival mechanism
Custom Fields live in `tabCustom Field` (database table), **not** in DocType JSON files. During `bench migrate`, schema sync overwrites core fields from JSON, then re-applies Custom Fields and Property Setters on top. Custom fields **survive app updates**; direct modifications to core DocType JSON fields **get overwritten**.

### Fixtures in hooks.py
```python
fixtures = [
    {"dt": "Custom Field", "filters": [["name", "in", ["Sales Invoice-custom_field1"]]]},
    {"dt": "Property Setter", "filters": [["doc_type", "=", "Sales Invoice"]]},
]
```
Export: `bench --site sitename export-fixtures` → creates JSON in `<app>/fixtures/`. Auto-imported on install and migrate.

### Programmatic creation
```python
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
create_custom_fields({"Sales Invoice": [{"fieldname": "custom_gstin", "label": "GSTIN", "fieldtype": "Data", "insert_after": "company"}]})
```

### `get_custom_fields()`
```python
meta = frappe.get_meta("Sales Invoice")
meta.get_custom_fields()  # returns list of custom field objects
```

---

## 12. Site configuration

### `site_config.json` — location and key fields
Location: `frappe-bench/sites/{sitename}/site_config.json`

Essential keys: `db_name`, `db_password`, `db_type` ("mariadb"/"postgres"), `db_host`, `admin_password`, `encryption_key`.

Common keys: `developer_mode`, `mute_emails`, `maintenance_mode`, `pause_scheduler`, `server_script_enabled`, `max_file_size`, `host_name`, `allow_cors`.

### `common_site_config.json`
Location: `frappe-bench/sites/common_site_config.json`. Shared by all sites. Contains: `redis_cache`, `redis_queue`, `socketio_port`, `webserver_port`, `gunicorn_workers`, `background_workers`.

**Precedence:** `site_config.json` overrides `common_site_config.json`.

### `frappe.conf` API
```python
import frappe
db_name = frappe.conf.db_name
api_key = frappe.conf.get("my_api_key")
```
`frappe.conf` is a cached `_dict` loaded at init. Use `frappe.get_site_config()` for fresh on-disk reads.

### `bench set-config`
```bash
bench --site mysite set-config key value          # site-level
bench set-config -g key value                      # bench-level (common_site_config)
```

### Storing secrets properly
**Option 1:** Put in `site_config.json`, access via `frappe.conf.get("my_secret")`.  
**Option 2:** Use a Settings Single DocType with Password fieldtype, retrieve via `frappe.utils.password.get_decrypted_password("My Settings", "My Settings", "api_secret")`.

**v15 change:** `server_script_enabled` defaults to `false` — must be explicitly enabled.

---

## 13. Advanced permission patterns

### `frappe.has_permission()` — exact signature
```python
frappe.has_permission(
    doctype,         # str: DocType name
    ptype="read",    # "read", "write", "create", "delete", "submit", "cancel", etc.
    doc=None,        # str or Document: specific document
    user=None,       # str: user email (defaults to current user)
    throw=False,     # bool: raise PermissionError instead of returning False
)
```

### `frappe.permissions.add_user_permission()`
```python
frappe.permissions.add_user_permission(
    doctype, name, user, ignore_permissions=False, applicable_for=None
)
```

### User Permissions (row-level)
User Permissions **restrict**, not grant. They filter which records a user can see based on Link field values. Key fields: `allow` (DocType), `for_value` (document name), `user`, `applicable_for` (optional — limit to specific DocType), `apply_to_all_doctypes`.

### Permission Level (field-level)
Each field has `permlevel` (0, 1, 2...). Different roles can get read/write on different permlevels via the DocPerm table. Permlevel 0 is default for all fields.

### `frappe.only_for(roles)`
**Not a decorator** — called inline. Raises `frappe.PermissionError` if current user lacks the specified role(s).
```python
frappe.only_for("Script Manager", True)
```

### Permission query conditions (hooks.py)
```python
permission_query_conditions = {"Sales Invoice": "myapp.permissions.get_conditions"}
```
```python
def get_conditions(user):
    if user == "Administrator": return ""
    return f"`tabSales Invoice`.owner = {frappe.db.escape(user)}"
```
Returns a SQL WHERE clause string.

### `has_permission` hook
```python
# hooks.py
has_permission = {"My DocType": "myapp.permissions.has_permission"}
# Function: def has_permission(doc, ptype, user): return True/False/None
```
Return `None` to defer to standard checks. Only `False` explicitly denies.

### `ignore_permissions` flag
```python
frappe.get_list("DocType", ignore_permissions=True)
doc.insert(ignore_permissions=True)
doc.flags.ignore_permissions = True; doc.save()
```
**Note:** `frappe.get_all()` is `frappe.get_list()` with `ignore_permissions=True` as default.

---

## 14. Bench multisite architecture

### Directory structure
```
frappe-bench/
├── apps/                          # Shared app code
├── sites/
│   ├── common_site_config.json    # Bench-level config
│   ├── currentsite.txt            # Default site name
│   ├── assets/                    # Built static assets
│   ├── site1.local/
│   │   ├── site_config.json
│   │   ├── private/files/         # Private uploads (/private/files/*)
│   │   └── public/files/          # Public uploads (/files/*)
│   └── site2.example.com/
│       ├── site_config.json
│       ├── private/files/
│       └── public/files/
```

### Site resolution
**Production:** Nginx preserves the `Host` header → Frappe matches it to a `sites/{hostname}/` directory.  
**Development:** Falls back to `currentsite.txt`.

### Key commands
```bash
bench new-site sitename [--db-type mariadb|postgres] [--admin-password X] [--install-app erpnext]
bench use sitename              # Sets currentsite.txt
bench --site sitename migrate
bench --site all migrate        # All sites
bench setup nginx               # Generate nginx config for multitenancy
```

---

## 15. Frappe utility functions

**Import:** `from frappe.utils import <function>` (all re-exported from `frappe/utils/data.py`).

### Date/time
```python
now() -> str           # "YYYY-MM-DD HH:MM:SS.ffffff"
nowdate() -> str       # "YYYY-MM-DD"
today() -> str         # Alias for nowdate()
nowtime() -> str       # "HH:MM:SS.ffffff"
add_days(date, days) -> datetime.date
add_months(date, months) -> datetime.date
add_years(date, years) -> datetime.date
date_diff(date1, date2) -> int          # days
time_diff(end, start) -> timedelta
time_diff_in_seconds(end, start) -> float
getdate(string_date=None) -> datetime.date
get_datetime(string=None) -> datetime.datetime
get_time(time_str) -> datetime.time
```

### Type conversion
```python
flt(s, precision=None, rounding_method=None) -> float   # Returns 0.0 on failure
cint(s, default=0) -> int                               # Returns 0 on failure
cstr(s, encoding="utf-8") -> str
```

### Formatting
```python
fmt_money(amount, precision=None, currency=None, format=None) -> str
money_in_words(number, main_currency=None, fraction_currency=None) -> str
```

### URL and user
```python
get_url(uri=None, full_address=False) -> str    # Site URL
get_fullname(user=None) -> str                   # Full name of user
```

### Random/hash
```python
random_string(length) -> str                    # alphanumeric
frappe.generate_hash(txt=None, length=56) -> str  # SHA-224 hex digest (on frappe, not frappe.utils)
```

### HTML/string
```python
strip_html(html_text) -> str                    # Remove HTML tags
sanitize_html(html) -> str                      # XSS-safe HTML (from frappe.utils.html_utils)
comma_and(some_list, add_quotes=True) -> str    # '"a", "b" and "c"'
comma_or(some_list, add_quotes=True) -> str     # '"a", "b" or "c"'
unique(seq) -> list                             # Deduplicate preserving order
```

**Common AI mistakes:** Importing `generate_hash` from `frappe.utils` (it's on `frappe` itself). Using `frappe.utils.now_datetime()` when `frappe.utils.now()` returns a string. Confusing `nowdate()` (string) with `getdate()` (date object).

---

## 16. Dashboard Charts and Number Cards

### Dashboard Chart DocType key fields
`chart_name`, `chart_type` (Count/Sum/Average/Group By/Custom/Report), `document_type`, `based_on` (date field for time series), `value_based_on` (numeric field for Sum/Average), `timespan`, `time_interval`, `filters_json`, `type` (Line/Bar/Percentage/Pie/Donut), `source` (for Custom type), `report_name` (for Report type).

### Custom chart source pattern
```python
# Whitelisted method returning chart data
@frappe.whitelist()
def get_chart_data(filters=None):
    return {
        "labels": ["Jan", "Feb", "Mar"],
        "datasets": [{"values": [23, 45, 56], "name": "Revenue"}],
        "type": "bar",
    }
```
JS registration: `frappe.dashboards.chart_sources["My Source"] = { method: "myapp.api.get_chart_data", filters: [...] };`

### Number Card DocType
Types: `Document Type`, `Report`, `Custom`. Key fields: `function` (Count/Sum/Average/Min/Max), `aggregate_function_based_on`, `filters_json`, `method` (dotted path for Custom type).

Custom Number Card method must return: `{"value": 50, "fieldtype": "Currency"}`.

### Dashboard DocType
Groups multiple charts via `charts` child table (`Dashboard Chart Link` with `chart` Link and `width` Half/Full).

---

## 17. Workspace customization (v15/v16)

### Workspace DocType key fields
`title`, `module`, `icon`, `public` (1=PUBLIC sidebar, 0=MY WORKSPACES), `for_user`, `parent_page`, `sequence_id`, `roles` (child table for access control), `content` (JSON-encoded block layout), `links`, `shortcuts`, `charts`, `number_cards`, `custom_blocks`.

### Block types in `content` JSON
`"header"`, `"shortcut"`, `"card"`, `"chart"`, `"number_card"`, `"custom_block"` (v15+), `"spacer"`, `"text"`, `"onboarding"`. Each block has `id`, `type`, `data` (block-specific config).

### v14 → v15 changes
Removed: `category`, `extends_another_page`, `pin_to_top`, `pin_to_bottom`. Added: `public`, `for_user`, `parent_page`, `roles`, `sequence_id`, `restrict_to_domain`, `content` (block-based layout). Workspace files moved to `<app>/<module>/workspace/<name>/<name>.json`.

### Fixture export for workspaces
```python
fixtures = [{"dt": "Workspace", "filters": [["module", "=", "My Module"]]}]
```

---

## 18. Data Import tool

### Data Import DocType
Key fields: `reference_doctype`, `import_type` ("Insert New Records"/"Update Existing Records"), `import_file` (Attach), `submit_after_import`, `mute_emails`, `status` (Pending/Success/Partial Success/Error).

### CSV format
Headers use field labels or fieldnames. Date format: `YYYY-MM-DD`. Link fields use the `name` value. Check fields: `0`/`1`.

### Child table format
```csv
ID,Customer,Posting Date,items:item_code,items:qty,items:rate
,CUST-001,2024-01-15,ITEM-A,10,100
,,,ITEM-B,5,200
```
Each child row is a separate CSV row. Parent fields are repeated or left blank after the first row.

### Programmatic import
```python
from frappe.core.doctype.data_import.data_import import import_file
import_file(doctype="Customer", file_path="/path/to/file.csv", import_type="Insert",
            submit_after_import=False, console=False)
```

**CLI:** `bench --site <site> data-import --file /path.csv --doctype Customer --type Insert`

### Importer class
```python
from frappe.core.doctype.data_import.importer import Importer
i = Importer(doctype="Customer", data_import=data_import_doc, file_path="/path.csv")
i.import_data()
```

---

## 19. Webhook DocType

### Key fields
`enabled`, `webhook_doctype`, `webhook_docevent`, `condition` (Python expression), `request_url`, `is_dynamic_url` (Jinja in URL), `request_method` (POST/PUT/DELETE), `request_structure` (""/"Form URL-Encoded"/"JSON"), `webhook_data` (child table for Form URL-Encoded), `webhook_json` (Jinja template for JSON), `webhook_headers` (child table), `enable_security`, `webhook_secret`.

### Supported events
`after_insert`, `on_update`, `on_submit`, `on_cancel`, `on_trash`, `on_update_after_submit`, `on_change`. Submit/cancel/update_after_submit require submittable DocTypes.

### Request structure
**Form URL-Encoded:** `webhook_data` child table maps `key` → `fieldname`.  
**JSON:** `webhook_json` field uses Jinja with `{{ doc.name }}`, `{{ doc.status }}`, etc.

### Secret verification
When `enable_security` is checked, adds header **`X-Frappe-Webhook-Signature`** containing a **base64-encoded HMAC-SHA256** hash of the JSON payload using `webhook_secret` as the key.

### Execution flow
Webhooks are queued during the request, fired **after DB commit** (`frappe.db.after_commit`), then executed as **background jobs** via `frappe.enqueue()`. Results are logged in the **Webhook Request Log** DocType.

### Condition field
```python
doc.status == "Approved"
doc.grand_total > 10000
```
Evaluated with `frappe.safe_eval()` with `doc` in context.

---

## 20. Document naming series

### `autoname` property options

| Format | Example | Result |
|--------|---------|--------|
| `field:{fieldname}` | `field:article_name` | Value of the field |
| `naming_series:` | `naming_series:` | Uses `naming_series` field value |
| Pattern with `#` | `PRE.#####` | `PRE00001`, `PRE00002` |
| `Prompt` | `Prompt` | User enters manually |
| `hash` | `hash` | Random 10-char hash |
| `autoincrement` | `autoincrement` | DB auto-increment integer |
| `format:{pattern}` | `format:PRE-{YYYY}-{#####}` | `PRE-2024-00001` |

### Format tokens
`.YYYY.`/`{YYYY}` (4-digit year), `.YY.`/`{YY}` (2-digit), `.MM.`/`{MM}` (month), `.DD.`/`{DD}` (day), `.#####`/`{#####}` (counter — number of `#` controls zero-padding), `{fieldname}` (document field value).

### Key functions from `frappe/model/naming.py`
```python
def make_autoname(key="", doctype="", doc=None) -> str
def getseries(key, digits, doctype="") -> str
def parse_naming_series(parts, doctype="", doc=None) -> str
def revert_series_if_last(key, name, doc=None)
```

### Series tracking
The **`tabSeries`** table stores `name` (prefix key) and `current` (integer counter). Each call to `getseries()` atomically increments the counter using `SELECT ... FOR UPDATE`.

### Controller override
```python
class MyDoc(Document):
    def autoname(self):
        self.name = make_autoname(f"PRE-{self.category}-.#####", doc=self)
```

### `naming_series` field
If a DocType has a Select field named `naming_series`, set `autoname = "naming_series:"`. The field's options define available patterns:
```
INV-.YYYY.-.#####
SINV-.YYYY.-.#####
```

### Document Naming Rule DocType
Allows conditional naming rules per DocType: set prefix, digits, and conditions. Multiple rules can apply different series based on document field values.

### `name` field constraints
Must be unique per DocType. Max **140 characters** (VARCHAR(140)). Cannot contain certain special characters.

**Common AI mistakes:** Using `{YYYY}` inside `.` delimiters (either `{YYYY}` in format strings OR `.YYYY.` in naming series, never both). Calling `getseries()` without proper locking context. Setting `autoname` in the DocType JSON while also expecting `naming_series` to work without `naming_series:` prefix.