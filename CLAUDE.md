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

### Controller Lifecycle Events (in order)

```
autoname → before_validate → validate → before_save →
before_insert (new) → after_insert (new) → on_update →
on_submit → on_cancel → on_trash
```

### Python Controller Template

```python
import frappe
from frappe.model.document import Document

class MyDoctype(Document):
    def validate(self):
        """Runs before save. Raise frappe.ValidationError to block."""
        if not self.required_field:
            frappe.throw("Required field is mandatory")

    def on_submit(self):
        """Runs when document is submitted."""
        self.create_related_records()

    def on_cancel(self):
        """Runs when document is cancelled."""
        self.reverse_related_records()

    def before_insert(self):
        """Runs only for new documents, before DB insert."""
        pass

    def after_insert(self):
        """Runs only for new documents, after DB insert."""
        pass

    def on_update(self):
        """Runs after every save (insert or update)."""
        pass

    def on_trash(self):
        """Runs before document is deleted."""
        pass
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

### Frappe ORM Quick Reference

```python
# Get single document
doc = frappe.get_doc("Sales Order", "SO-001")

# Get list with filters
items = frappe.get_list("Item",
    filters={"item_group": "Products"},
    fields=["name", "item_name", "standard_rate"],
    order_by="item_name asc",
    limit_page_length=20
)

# Get single value
name = frappe.db.get_value("Customer", {"email_id": "x@y.com"}, "customer_name")

# Set single value
frappe.db.set_value("Item", "ITEM-001", "item_name", "Updated Name")

# SQL (escape inputs!)
results = frappe.db.sql("""
    SELECT name, grand_total FROM `tabSales Order`
    WHERE customer = %s AND docstatus = 1
""", (customer_name,), as_dict=True)

# Create new document
doc = frappe.get_doc({
    "doctype": "ToDo",
    "description": "Follow up",
    "assigned_by": frappe.session.user
})
doc.insert(ignore_permissions=False)

# Delete document
frappe.delete_doc("ToDo", "TODO-001")

# Check existence
exists = frappe.db.exists("Customer", "CUST-001")

# Count
count = frappe.db.count("Sales Order", filters={"status": "Draft"})
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

# Jinja environment customization
jinja = {
    "methods": ["my_app.utils.my_jinja_method"],
}
```

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

## Checklist Before Creating Any Item

- [ ] Identified which app this belongs to (ERPNext / Helpdesk / CRM / custom)
- [ ] Using correct DocType naming prefix (none / HD / CRM)
- [ ] Creating in correct directory path
- [ ] Using correct frontend pattern for the target app
- [ ] Added hooks in `hooks.py` if extending existing DocTypes
- [ ] Will run `bench --site {site} migrate` after DocType changes
- [ ] Tests written in `test_*.py`
