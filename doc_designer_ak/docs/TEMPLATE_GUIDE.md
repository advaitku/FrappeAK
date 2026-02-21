# AK Document Designer — Template Guide

This guide covers everything you need to know to create document templates for Doc Designer AK. Templates are written as HTML + Jinja2 and are designed to be created and edited by Claude AI.

---

## What Is a Template?

An **AK Document Template** is an HTML document with embedded Jinja2 syntax. It defines:

1. **Merge fields** — dynamic values pulled from a Frappe document (e.g. `{{ doc.customer_name }}`)
2. **Interactive fields** — form inputs the recipient can fill in (e.g. `{{ ak_input("po_number", label="PO Number") }}`)
3. **Layout and styling** — using the built-in CSS classes (see LAYOUT_REFERENCE.md)
4. **Action buttons** — Accept/Decline or Submit buttons

Templates are stored in the **AK Document Template** DocType and rendered server-side via Jinja2 before being served to the recipient on a guest-accessible web page.

---

## Two Modes

### Document Mode (default)
Share an existing document (e.g. Sales Invoice SI-001). The template:
- Has access to the full document via `{{ doc.field_name }}`
- Pre-fills interactive fields from existing document values
- Updates the original document when the recipient submits (for existing fields)
- Always creates an AK Document Response record

### Public Form Mode
Generate a blank form via a generic link. The template:
- `doc` is an empty dictionary — no document fields available
- Interactive fields start empty (or with defaults)
- Creates a **NEW** record of the reference DocType on submit
- Useful for contact forms, feedback forms, registration

Set `Is Public Form = 1` on the template to enable this mode.

---

## Jinja2 Basics

### Output Values
```html
{{ doc.customer_name }}
{{ doc.posting_date }}
{{ doc.grand_total }}
```

### Formatted Values
```html
{{ frappe.utils.fmt_money(doc.grand_total, currency="USD") }}
{{ frappe.utils.formatdate(doc.posting_date) }}
{{ format_currency(doc.grand_total) }}
```

### Conditional Logic
```html
{% if doc.status == "Overdue" %}
  <div class="ak-notice">This invoice is overdue!</div>
{% endif %}

{% if doc.grand_total > 10000 %}
  {{ ak_input("po_number", label="Purchase Order Number", mandatory=True) }}
{% endif %}
```

### Loops (Child Tables)
```html
{% for item in doc.items %}
  <p>{{ item.item_name }} — Qty: {{ item.qty }}</p>
{% endfor %}
```

### Default Values and Filters
```html
{{ doc.customer_name or "N/A" }}
{{ doc.description | truncate(100) }}
{{ doc.posting_date | default("Not set") }}
```

---

## Template Structure

A typical template follows this structure:

```html
<div class="ak-document">
  <!-- Header with branding and document info -->
  <div class="ak-header">
    <h1>Invoice {{ doc.name }}</h1>
    <p>Date: {{ doc.posting_date }}</p>
  </div>

  <!-- Content sections -->
  <div class="ak-section">
    <h3>Bill To</h3>
    <p><strong>{{ doc.customer_name }}</strong></p>
    <p>{{ doc.address_display }}</p>
  </div>

  <!-- Items/pricing table -->
  {{ ak_items_table(doc) }}

  <!-- Interactive fields -->
  <div class="ak-section">
    {{ ak_date("preferred_payment_date", label="Preferred Payment Date", mandatory=True) }}
    {{ ak_textarea("comments", label="Comments") }}
  </div>

  <!-- Action buttons -->
  {{ ak_accept_decline(accept_label="Approve", decline_label="Dispute") }}
</div>
```

---

## Template Sections

The AK Document Template DocType has several HTML fields:

| Field | Purpose | When Shown |
|---|---|---|
| `template_html` | Main document body | Always |
| `header_html` | Repeated header (for PDF pagination) | Every page |
| `footer_html` | Repeated footer (for PDF pagination) | Every page |
| `cover_page_html` | Optional first/cover page | Before main body |
| `custom_css` | Additional CSS styles | Applied to page |

### Cover Page
```html
<h1 style="font-size: 36px; margin-bottom: 16px;">PROPOSAL</h1>
<p style="font-size: 18px; color: #6b7280;">{{ doc.customer_name }}</p>
<p>Prepared on {{ frappe.utils.formatdate(nowdate()) }}</p>
```

### Header (PDF)
```html
<div style="display: flex; justify-content: space-between; font-size: 11px; color: #9ca3af;">
  <span>{{ doc.company }}</span>
  <span>{{ doc.name }}</span>
</div>
```

### Footer (PDF)
```html
<div style="text-align: center; font-size: 10px; color: #9ca3af;">
  Confidential — {{ doc.company }}
</div>
```

---

## Available Context Variables

When your template renders, these variables are available:

| Variable | Type | Description |
|---|---|---|
| `doc` | Document | The Frappe document being shared (or empty dict for public forms) |
| `frappe` | Module | Access to `frappe.utils`, `frappe.format`, `frappe.get_url` |
| `share` | Document | The AK Document Share record |
| `nowdate` | Function | Returns today's date string |
| `format_currency` | Function | `frappe.utils.fmt_money()` |
| `template_fields` | List[dict] | The template's field definitions |
| `ak_input` | Function | Render text input (see HELPER_FUNCTIONS.md) |
| `ak_textarea` | Function | Render textarea |
| `ak_date` | Function | Render date picker |
| `ak_datetime` | Function | Render datetime picker |
| `ak_checkbox` | Function | Render checkbox |
| `ak_select` | Function | Render dropdown select |
| `ak_field_table` | Function | Auto-render all defined fields as a table |
| `ak_items_table` | Function | Render items/pricing table |
| `ak_accept_decline` | Function | Render Accept/Decline buttons |
| `ak_submit_button` | Function | Render Submit button |

---

## Interactive Fields

Interactive fields are form inputs that the recipient can fill in. There are two ways to add them:

### 1. Inline Helper Functions (in template_html)
Call the helper functions directly where you want the field to appear:

```html
{{ ak_input("customer_po", label="Your PO Number", mandatory=True) }}
{{ ak_date("delivery_date", label="Preferred Delivery Date", value=doc.delivery_date, editable=True) }}
{{ ak_textarea("special_instructions", label="Special Instructions") }}
```

### 2. Auto-Generated Field Table
Define fields in the **Interactive Fields** child table on the template, then render them all at once:

```html
{{ ak_field_table(columns=1) }}
```

Or in two columns:
```html
{{ ak_field_table(columns=2) }}
```

The child table fields control:
- **field_name** — the programmatic name
- **field_label** — the display label
- **field_type** — Data, Text, Date, Select, Check, etc.
- **is_existing_field** — maps to a real DocType field (pre-fills from doc, writes back on submit)
- **is_editable** — can the recipient change this?
- **is_mandatory** — is it required?
- **default_value** — initial value
- **column** — Full Width, Left, or Right (for 2-column layout)

### Pre-filling from Document
When `is_existing_field` is checked and a document is shared:
```html
<!-- This pre-fills with doc.delivery_date and writes back on submit -->
{{ ak_date("delivery_date", label="Delivery Date", value=doc.delivery_date, editable=True, mandatory=True) }}
```

### Custom Fields (not on DocType)
Fields without `is_existing_field` are stored only in the AK Document Response:
```html
{{ ak_input("recipient_feedback", label="Your Feedback") }}
```

---

## Action Buttons

Every template needs at least one action button for the recipient to submit their response.

### Accept/Decline Pattern
For documents that need approval:
```html
{{ ak_accept_decline(accept_label="Approve Invoice", decline_label="Dispute Invoice") }}
```
This creates two buttons:
- **Accept** → sets response_type to "Accepted"
- **Decline** → sets response_type to "Declined"

### Simple Submit Pattern
For forms and data collection:
```html
{{ ak_submit_button(label="Submit Response") }}
```
This creates one button that sets response_type to "Submitted".

---

## Conditional Logic Examples

### Show different content based on document status
```html
{% if doc.status == "Draft" %}
  <div class="ak-notice">This is a draft and may change.</div>
{% elif doc.status == "Overdue" %}
  <div class="ak-notice" style="background: #fef2f2; border-color: #ef4444; color: #dc2626;">
    Payment is overdue. Please remit immediately.
  </div>
{% endif %}
```

### Show fields based on amount
```html
{% if doc.grand_total > 50000 %}
  <div class="ak-section">
    <h3>Additional Approval Required</h3>
    {{ ak_input("approver_name", label="Approver Name", mandatory=True) }}
    {{ ak_input("approver_title", label="Approver Title", mandatory=True) }}
  </div>
{% endif %}
```

### Show/hide based on custom conditions
```html
{% if doc.items | length > 5 %}
  <div class="ak-notice">This order contains {{ doc.items | length }} items.</div>
{% endif %}
```

---

## Page Breaks (for PDF)

Insert a page break for PDF generation:
```html
<div class="ak-page-break"></div>
```

Use it between major sections:
```html
<div class="ak-section">
  <!-- Section 1: Terms and conditions -->
</div>

<div class="ak-page-break"></div>

<div class="ak-section">
  <!-- Section 2: Pricing details -->
</div>
```

---

## Email Template

The template's **Email Settings** section contains `email_subject` and `email_body_html`. These also support Jinja2:

### Email Subject
```
Invoice {{ doc.name }} from {{ doc.company }} — Please Review
```

### Email Body
```html
<p>Dear {{ doc.customer_name }},</p>
<p>Please review the attached invoice <strong>{{ doc.name }}</strong> for {{ format_currency(doc.grand_total) }}.</p>
<p><a href="{{ share_url }}">Click here to view and respond</a></p>
<p>This link expires on {{ frappe.utils.formatdate(share.expires_at) }}.</p>
<p>Thank you,<br>{{ doc.company }}</p>
```

The email context has access to: `doc`, `share`, `share_url`, `frappe`, `format_currency`, `nowdate`.

---

## Tips for Claude-Generated Templates

1. **Always wrap content in `<div class="ak-document">`** — this applies the base container styling
2. **Use semantic CSS classes** from LAYOUT_REFERENCE.md instead of inline styles where possible
3. **Test with both modes** — ensure the template works when `doc` is populated and when it's empty
4. **Escape user content** — Jinja2 auto-escapes by default, but be careful with `{{ doc.description | safe }}` (only use `| safe` for fields you trust)
5. **Keep templates simple** — complex logic should be in the Frappe backend, not in template HTML
6. **Always include an action button** — either `ak_accept_decline()` or `ak_submit_button()`
7. **Document your fields** — add all interactive fields to the child table even if you also use inline helpers, so the system knows about them for validation
