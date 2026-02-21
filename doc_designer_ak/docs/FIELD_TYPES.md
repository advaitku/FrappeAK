# AK Document Designer — Field Types Reference

This document covers all supported field types in AK Template Fields and how data flows between the template, the guest page, and Frappe.

---

## Supported Field Types

| Field Type | HTML Element | Input Type | Value Format |
|---|---|---|---|
| Data | `<input>` | text | String |
| Text | `<textarea>` | — | Multi-line string |
| Small Text | `<input>` | text | String |
| Int | `<input>` | number | Integer |
| Float | `<input>` | number | Decimal number |
| Currency | `<input>` | number | Decimal number |
| Date | `<input>` | date | YYYY-MM-DD |
| Datetime | `<input>` | datetime-local | YYYY-MM-DDTHH:MM |
| Check | `<input>` | checkbox | 1 or 0 |
| Select | `<select>` | — | Selected option string |

---

## Field Type Details

### Data
General-purpose text input. Suitable for names, email addresses, phone numbers, short text.

```html
{{ ak_input("customer_po", label="PO Number") }}
{{ ak_input("contact_email", label="Email", input_type="email") }}
{{ ak_input("phone", label="Phone", input_type="tel") }}
```

### Text
Multi-line textarea for longer text. Uses `<textarea>` element.

```html
{{ ak_textarea("comments", label="Comments", rows=4) }}
{{ ak_textarea("description", label="Description", rows=8) }}
```

### Small Text
Rendered as a single-line text input (same as Data). Used when the DocType field is Small Text.

### Int
Numeric input that accepts whole numbers only. Renders with `type="number"`.

```html
{{ ak_input("quantity", label="Quantity", input_type="number") }}
```

### Float
Numeric input that accepts decimal numbers. Renders with `type="number"`.

```html
{{ ak_input("discount_percent", label="Discount %", input_type="number") }}
```

### Currency
Numeric input for monetary values. Renders with `type="number"`.

```html
{{ ak_input("approved_amount", label="Approved Amount", input_type="number") }}
```

### Date
Date picker that opens the browser's native date picker.

```html
{{ ak_date("delivery_date", label="Delivery Date") }}
```

Value format: `YYYY-MM-DD` (e.g., `2026-03-15`)

### Datetime
Date and time picker using the browser's native datetime-local picker.

```html
{{ ak_datetime("meeting_time", label="Meeting Time") }}
```

Value format: `YYYY-MM-DDTHH:MM` (e.g., `2026-03-15T14:30`)

The helper auto-converts Frappe's `YYYY-MM-DD HH:MM:SS` format to the HTML `datetime-local` format.

### Check
Checkbox for boolean values. Returns `1` (checked) or `0` (unchecked).

```html
{{ ak_checkbox("agree_terms", label="I agree to the terms") }}
```

### Select
Dropdown with predefined options.

```html
{{ ak_select("status", label="Status", options=["Pending", "Approved", "Rejected"]) }}
```

Options can be provided as:
- A Python list: `["Option A", "Option B"]`
- A newline-separated string: `"Option A\nOption B"`

In the AK Template Field child table, enter one option per line in the Options field.

---

## Data Flow

### Document Mode (sharing an existing document)

```
1. Share Created
   └─► Template + Document loaded
       └─► For each field where is_existing_field = 1:
           └─► Pre-fill value from doc.{field_name}

2. Recipient Opens Link
   └─► Guest page renders with pre-filled fields
       └─► Editable fields can be modified
       └─► Read-only fields are disabled

3. Recipient Submits
   └─► JavaScript collects all editable field values
   └─► POST to /api/method/doc_designer_ak.api.submit_response
       ├─► AK Document Response created (stores ALL field values as JSON)
       ├─► For each is_existing_field + is_editable field:
       │   └─► Original document field updated
       └─► Share status updated (Submitted/Accepted/Declined)
```

### Public Form Mode (creating a new record)

```
1. Share Created (no reference_name)
   └─► Template loaded, doc is empty dict

2. Recipient Opens Link
   └─► Guest page renders with empty/default fields
       └─► All editable fields can be filled

3. Recipient Submits
   └─► JavaScript collects all editable field values
   └─► POST to /api/method/doc_designer_ak.api.submit_response
       ├─► NEW document created in reference_doctype
       │   └─► is_existing_field values set on new doc
       ├─► AK Document Response created (stores ALL field values + new doc name)
       └─► Share status updated
```

---

## Existing Field vs Custom Field

### Existing Field (`is_existing_field = 1`)
- **Pre-fills** from the document's actual field value
- **Writes back** to the original document on submission
- The `field_name` must match an actual field on the DocType
- Example: `delivery_date` on a Sales Order

### Custom Field (`is_existing_field = 0`)
- **Does not pre-fill** from the document (uses `default_value` if set)
- **Does not write back** to any document
- Stored only in the AK Document Response's `response_data` JSON
- The `field_name` can be anything
- Example: `recipient_feedback`, `satisfaction_rating`

---

## Validation Rules

### Client-Side (JavaScript)
- Mandatory fields are validated before submission
- Fields with `data-mandatory="1"` must have a non-empty value
- Error styling (red border) is applied to empty mandatory fields
- A toast message "Please fill in all required fields" is shown

### Server-Side (Python)
- The `submit_response` API re-validates mandatory fields from the template definition
- Fields where `is_mandatory = 1` AND `is_editable = 1` must have a value
- Non-editable fields are not collected from the form (they keep their original values)

---

## Type Coercion

When field values are submitted and written back to the original document:

| Field Type | Submitted As | Written Back As |
|---|---|---|
| Data, Text, Small Text | string | string |
| Int | string | The string is set on the document; Frappe auto-casts to int |
| Float, Currency | string | The string is set on the document; Frappe auto-casts to float |
| Date | "YYYY-MM-DD" | string (Frappe date format) |
| Datetime | "YYYY-MM-DDTHH:MM" | string (needs server-side conversion) |
| Check | "1" or "0" | "1" or "0" (Frappe treats as int) |
| Select | string | string |

---

## AK Template Field Child Table Schema

When defining fields in the Interactive Fields table on AK Document Template:

| Column | Type | Required | Description |
|---|---|---|---|
| Field Name | Data | Yes | Programmatic name (e.g., `delivery_date`) |
| Field Label | Data | No | Display label (e.g., "Preferred Delivery Date") |
| Field Type | Select | Yes | One of the 10 supported types |
| Options | Small Text | No | For Select type: one option per line |
| Is Existing Field | Check | No | Maps to a real DocType field |
| Is Editable | Check | No | Default: Yes. If No: read-only display |
| Is Mandatory | Check | No | Default: No. If Yes: required for submission |
| Default Value | Data | No | Initial value for empty fields |
| Column | Select | No | Full Width, Left, or Right (for 2-col layout) |
