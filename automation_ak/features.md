# AutomationAK - Features

AutomationAK is a visual automation and workflow builder for the Frappe Framework. It lets you create no-code automation rules directly from the Frappe Desk UI -- define a trigger, set conditions, and chain actions that execute automatically when documents change.

## Triggers

Each automation rule targets a specific DocType and fires on one of four trigger types:

| Trigger | How it works |
|---------|-------------|
| **On Create** | Fires when a new document is inserted |
| **On Update (includes Create)** | Fires on every save, including the first. Optionally watches a specific field so it only fires when that field changes |
| **Time Interval** | Runs on a cron schedule (e.g. `0 9 * * 1` for every Monday at 9 AM). Evaluates conditions against all matching documents each time |
| **Macro (Button)** | Adds a clickable button to the form. Users trigger the automation manually |

**Recurrence control** -- choose "Every Time Conditions Are Met" or "Only First Time Conditions Are Met" (skips if the automation already ran successfully for that document).

## Conditions

Conditions are split into two groups that combine as **All (AND)** + **Any (OR)**:

- All Conditions -- every row must pass
- Any Conditions -- at least one row must pass
- No conditions -- the automation always runs

### Operators by field type

**Text / Data fields:**
`is`, `is not`, `contains`, `does not contain`, `starts with`, `ends with`, `is empty`, `is not empty`, `has changed`, `has changed to`, `has changed from`

**Numeric fields (Int, Float, Currency, Percent):**
`=`, `!=`, `>`, `<`, `>=`, `<=`, `between`, `is empty`, `is not empty`, `has changed`

**Date / Datetime fields:**
`is`, `is not`, `before`, `after`, `between`, `is today`, `is tomorrow`, `is yesterday`, `less than days ago`, `more than days ago`, `less than days later`, `more than days later`, `is empty`, `is not empty`

**Select fields:**
`is`, `is not`, `has changed`, `has changed to`, `has changed from`

**Link fields:**
`is`, `is not`, `is empty`, `is not empty`, `has changed`

**Check fields:**
`is`, `is not`

Change detection (`has changed`, `has changed to`, `has changed from`) uses Frappe's built-in `_doc_before_save` to compare old vs. new values.

## Actions

Each automation can have multiple actions that execute in order. If any action fails, execution stops and the error is logged.

### Send Email
- To / CC / BCC with Jinja merge fields (`{{ doc.customer_name }}`)
- Subject and body support Jinja templates
- Optionally attach a Print Format PDF
- Can use a saved Email Template instead of inline body

### Send WhatsApp
- Sends via Meta Cloud API, Twilio, or a custom provider
- Template messages or free-text body
- Phone number field supports Jinja (e.g. `{{ doc.phone }}`)
- Provider credentials stored in AK Automation Settings

### Update Fields
- Set one or more fields on the current document
- Value types: Static Value, Expression, Use Field (copy from another field), Use Function, Today, Today + N Days, Today - N Days, Current User, Clear

### Field Formulas
- Same as Update Fields but intended for calculated values
- Expression examples: `annual_revenue / 12`, `amount * 1.1`
- Conditional expressions: `if status == 'Open' then 'Active' else 'Inactive' end`
- Built-in functions: `concat()`, `uppercase()`, `lowercase()`, `trim()`, `length()`, `round()`, `abs()`

### Create Record
- Creates a new document of any DocType
- Field-value mappings defined as JSON with Jinja support

### Create Todo
- Assigns a ToDo to a user with a description and due date
- Fields support Jinja merge tags

### Create Event
- Creates a calendar Event with subject, start/end date, and event type
- Fields support Jinja merge tags

### HTTP Request
- Makes an outbound HTTP call (GET, POST, PUT, DELETE)
- URL, headers, and body all support Jinja
- Useful for integrating with external APIs or webhooks

### Run Script
- Executes custom Python code in a restricted sandbox
- Has access to `doc`, `frappe`, and the automation context
- For advanced use cases that the built-in actions don't cover

## Macro Buttons

When an automation has trigger type "Macro (Button)", a button is automatically injected into the form toolbar of the target DocType. Clicking the button evaluates conditions and runs actions against the current document. The button label is configurable per automation.

## Execution Log

Every automation execution is recorded in the **AK Automation Log** DocType:

- Which automation ran, on which document
- Trigger type that fired it
- Status: Success, Failed, or Skipped (conditions not met)
- Per-action results stored as JSON
- Error traceback for failures
- Execution time in milliseconds

Logging can be toggled on/off in AK Automation Settings. Old logs are automatically cleaned up daily based on a configurable retention period (default: 30 days).

## Performance

- Active automations are cached in Redis per DocType + trigger type (5-minute TTL). Cache is rebuilt automatically on miss.
- Recursion prevention: a `frappe.flags` guard prevents the same automation from re-triggering itself when it updates the document.
- Field updates on `after_*` events use `frappe.db.set_value(..., update_modified=False)` to avoid re-triggering.

## DocTypes

| DocType | Type | Purpose |
|---------|------|---------|
| AK Automation | Main | The automation rule: trigger, conditions, actions, stats |
| AK Automation Condition | Child table | A single condition row (field, operator, value) |
| AK Automation Action | Child table | A single action row (type, config, email/WA/HTTP fields) |
| AK Field Update | Child table | Field update row for Update Fields / Field Formulas actions |
| AK Automation Log | Log | Execution history per automation per document |
| AK Automation Settings | Single | Global settings: WhatsApp credentials, logging toggle, log retention |

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `automation_ak.api.automation.get_doctype_fields` | Returns fields for a DocType (for condition/action dropdowns) |
| `automation_ak.api.automation.get_field_options` | Returns valid options for a Select field |
| `automation_ak.api.automation.get_operators_for_field` | Returns valid operators based on field type |
| `automation_ak.api.automation.run_button_automation` | Executes a Macro (Button) automation |
| `automation_ak.api.automation.test_automation` | Dry-run an automation against a real document |
| `automation_ak.api.automation.get_button_automations` | Lists active button automations for a DocType |
| `automation_ak.api.automation.test_whatsapp_connection` | Tests WhatsApp API credentials |
