# AK Document Designer — Helper Functions Reference

All helper functions are available in template HTML as Jinja2 functions. They generate safe HTML with the correct CSS classes and data attributes for the guest page JavaScript to handle form submission.

---

## ak_input

Renders a text input field.

### Signature
```python
ak_input(fieldname, label="", value="", placeholder="", editable=True, mandatory=False, input_type="text")
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `fieldname` | str | (required) | Field name used for form submission |
| `label` | str | `""` | Display label shown above the input |
| `value` | str | `""` | Pre-filled value |
| `placeholder` | str | `""` | Placeholder text |
| `editable` | bool | `True` | Whether the recipient can edit |
| `mandatory` | bool | `False` | Whether the field is required |
| `input_type` | str | `"text"` | HTML input type: `text`, `number`, `email`, `tel`, `url` |

### Usage
```html
{{ ak_input("customer_po", label="Purchase Order Number") }}
{{ ak_input("contact_email", label="Email", value=doc.email_id, input_type="email", mandatory=True) }}
{{ ak_input("total_units", label="Total Units", input_type="number") }}
{{ ak_input("company_name", label="Company", value=doc.customer_name, editable=False) }}
```

### Rendered HTML
```html
<div class="ak-field ak-field-mandatory" data-fieldname="customer_po" data-fieldtype="Data" data-editable="1" data-mandatory="1">
  <label class="ak-field-label">Purchase Order Number</label>
  <input type="text" name="customer_po" value="" required class="ak-field-input" />
</div>
```

---

## ak_textarea

Renders a multi-line text area.

### Signature
```python
ak_textarea(fieldname, label="", value="", rows=4, editable=True, mandatory=False, placeholder="")
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `fieldname` | str | (required) | Field name |
| `label` | str | `""` | Display label |
| `value` | str | `""` | Pre-filled value |
| `rows` | int | `4` | Number of visible text rows |
| `editable` | bool | `True` | Whether the recipient can edit |
| `mandatory` | bool | `False` | Whether required |
| `placeholder` | str | `""` | Placeholder text |

### Usage
```html
{{ ak_textarea("comments", label="Comments or Questions", placeholder="Enter any comments...") }}
{{ ak_textarea("terms", label="Terms & Conditions", value=doc.terms, editable=False, rows=8) }}
{{ ak_textarea("special_instructions", label="Special Instructions", mandatory=True, rows=3) }}
```

### Rendered HTML
```html
<div class="ak-field" data-fieldname="comments" data-fieldtype="Text" data-editable="1">
  <label class="ak-field-label">Comments or Questions</label>
  <textarea name="comments" rows="4" placeholder="Enter any comments..." class="ak-field-input"></textarea>
</div>
```

---

## ak_date

Renders a date picker input.

### Signature
```python
ak_date(fieldname, label="", value="", editable=True, mandatory=False)
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `fieldname` | str | (required) | Field name |
| `label` | str | `""` | Display label |
| `value` | str | `""` | Pre-filled date (YYYY-MM-DD format) |
| `editable` | bool | `True` | Whether the recipient can edit |
| `mandatory` | bool | `False` | Whether required |

### Usage
```html
{{ ak_date("delivery_date", label="Preferred Delivery Date", mandatory=True) }}
{{ ak_date("payment_date", label="Payment Date", value=doc.due_date) }}
{{ ak_date("posting_date", label="Invoice Date", value=doc.posting_date, editable=False) }}
```

### Rendered HTML
```html
<div class="ak-field ak-field-mandatory" data-fieldname="delivery_date" data-fieldtype="Date" data-editable="1" data-mandatory="1">
  <label class="ak-field-label">Preferred Delivery Date</label>
  <input type="date" name="delivery_date" value="" required class="ak-field-input" />
</div>
```

---

## ak_datetime

Renders a datetime picker input.

### Signature
```python
ak_datetime(fieldname, label="", value="", editable=True, mandatory=False)
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `fieldname` | str | (required) | Field name |
| `label` | str | `""` | Display label |
| `value` | str | `""` | Pre-filled datetime (Frappe format, converted to HTML datetime-local) |
| `editable` | bool | `True` | Whether the recipient can edit |
| `mandatory` | bool | `False` | Whether required |

### Usage
```html
{{ ak_datetime("meeting_time", label="Preferred Meeting Time", mandatory=True) }}
{{ ak_datetime("scheduled_at", label="Scheduled At", value=doc.scheduled_at, editable=False) }}
```

### Rendered HTML
```html
<div class="ak-field" data-fieldname="meeting_time" data-fieldtype="Datetime" data-editable="1">
  <label class="ak-field-label">Preferred Meeting Time</label>
  <input type="datetime-local" name="meeting_time" value="" class="ak-field-input" />
</div>
```

---

## ak_checkbox

Renders a checkbox input.

### Signature
```python
ak_checkbox(fieldname, label="", checked=False, editable=True)
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `fieldname` | str | (required) | Field name |
| `label` | str | `""` | Label shown next to the checkbox |
| `checked` | bool | `False` | Whether pre-checked |
| `editable` | bool | `True` | Whether the recipient can toggle |

### Usage
```html
{{ ak_checkbox("agree_terms", label="I agree to the terms and conditions") }}
{{ ak_checkbox("receive_updates", label="Send me email updates", checked=True) }}
{{ ak_checkbox("is_confirmed", label="Order confirmed", checked=doc.is_confirmed, editable=False) }}
```

### Rendered HTML
```html
<div class="ak-field" data-fieldname="agree_terms" data-fieldtype="Check" data-editable="1">
  <label class="ak-field-label ak-checkbox-label">
    <input type="checkbox" name="agree_terms" value="1" class="ak-field-input" />
    I agree to the terms and conditions
  </label>
</div>
```

---

## ak_select

Renders a dropdown select field.

### Signature
```python
ak_select(fieldname, label="", options=None, value="", editable=True, mandatory=False)
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `fieldname` | str | (required) | Field name |
| `label` | str | `""` | Display label |
| `options` | list or str | `[]` | List of option strings, or newline-separated string |
| `value` | str | `""` | Pre-selected option value |
| `editable` | bool | `True` | Whether the recipient can change |
| `mandatory` | bool | `False` | Whether required |

### Usage
```html
{{ ak_select("payment_method", label="Payment Method", options=["Bank Transfer", "Credit Card", "Check"], mandatory=True) }}

{{ ak_select("priority", label="Priority", options="Low\nMedium\nHigh", value="Medium") }}

{{ ak_select("delivery_method", label="Delivery", options=["Standard", "Express", "Same Day"], value=doc.delivery_method) }}
```

### Rendered HTML
```html
<div class="ak-field ak-field-mandatory" data-fieldname="payment_method" data-fieldtype="Select" data-editable="1" data-mandatory="1">
  <label class="ak-field-label">Payment Method</label>
  <select name="payment_method" required class="ak-field-input">
    <option value="">-- Select --</option>
    <option value="Bank Transfer">Bank Transfer</option>
    <option value="Credit Card">Credit Card</option>
    <option value="Check">Check</option>
  </select>
</div>
```

---

## ak_field_table

Auto-generates a form table from the template's **Interactive Fields** child table. This is the easiest way to render all defined fields without writing individual helper calls.

### Signature
```python
ak_field_table(columns=1)
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `columns` | int | `1` | Number of columns: `1` (full width) or `2` (side by side) |

### How It Works
- Reads field definitions from the AK Template Field child table
- Pre-fills values from the document for `is_existing_field` fields
- Respects `is_editable`, `is_mandatory`, `default_value`
- In 2-column mode, uses the `column` field (Left/Right) to position fields

### Usage
```html
<!-- Single column — all fields stacked vertically -->
{{ ak_field_table() }}

<!-- Two columns — fields arranged side by side -->
{{ ak_field_table(columns=2) }}
```

### Example Child Table Setup

| Field Name | Label | Type | Existing Field | Editable | Mandatory | Column |
|---|---|---|---|---|---|---|
| customer_name | Customer | Data | Yes | No | No | Left |
| contact_email | Email | Data | Yes | Yes | Yes | Right |
| delivery_date | Delivery Date | Date | Yes | Yes | Yes | Left |
| comments | Comments | Text | No | Yes | No | Full Width |

### Rendered HTML (2 columns)
```html
<table class="ak-field-table ak-two-col">
  <tbody>
    <tr>
      <td class="ak-col-left">
        <!-- customer_name (read-only, pre-filled) -->
      </td>
      <td class="ak-col-right">
        <!-- contact_email (editable, mandatory) -->
      </td>
    </tr>
    <tr>
      <td class="ak-col-left">
        <!-- delivery_date -->
      </td>
      <td class="ak-col-right"></td>
    </tr>
  </tbody>
</table>
<!-- comments rendered full width separately -->
```

---

## ak_items_table

Renders a pricing/items table from a document's `items` child table. Commonly used for invoices, quotations, and purchase orders.

### Signature
```python
ak_items_table(doc, columns=None, show_total=True, total_field="grand_total", currency_symbol="$")
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `doc` | Document | (required) | The Frappe document with an `items` child table |
| `columns` | list | `["item_name", "qty", "rate", "amount"]` | Column field names to display |
| `show_total` | bool | `True` | Show a totals row at the bottom |
| `total_field` | str | `"grand_total"` | Document field name for the total |
| `currency_symbol` | str | `"$"` | Currency symbol for monetary columns |

### Usage
```html
<!-- Default: item_name, qty, rate, amount + total -->
{{ ak_items_table(doc) }}

<!-- Custom columns -->
{{ ak_items_table(doc, columns=["item_code", "item_name", "qty", "rate", "amount"]) }}

<!-- No total row -->
{{ ak_items_table(doc, show_total=False) }}

<!-- Different total field -->
{{ ak_items_table(doc, total_field="net_total", currency_symbol="EUR ") }}
```

### Recognized Currency Columns
These columns are auto-formatted with the currency symbol: `rate`, `amount`, `net_amount`, `base_amount`.

The `qty` column is formatted as a plain number.

### Rendered HTML
```html
<table class="ak-items-table">
  <thead>
    <tr>
      <th class="ak-items-col-num">#</th>
      <th class="ak-items-col-item_name">Item Name</th>
      <th class="ak-items-col-qty">Qty</th>
      <th class="ak-items-col-rate">Rate</th>
      <th class="ak-items-col-amount">Amount</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="ak-items-col-num">1</td>
      <td class="ak-items-col-item_name">Widget A</td>
      <td class="ak-items-col-qty">10</td>
      <td class="ak-items-col-rate">$25.00</td>
      <td class="ak-items-col-amount">$250.00</td>
    </tr>
  </tbody>
  <tfoot>
    <tr class="ak-items-total">
      <td colspan="4"><strong>Total</strong></td>
      <td><strong>$250.00</strong></td>
    </tr>
  </tfoot>
</table>
```

---

## ak_accept_decline

Renders Accept and Decline action buttons. Use for documents that need approval/rejection (invoices, quotations, proposals).

### Signature
```python
ak_accept_decline(accept_label="Accept", decline_label="Decline")
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `accept_label` | str | `"Accept"` | Text on the accept button |
| `decline_label` | str | `"Decline"` | Text on the decline button |

### Usage
```html
{{ ak_accept_decline() }}
{{ ak_accept_decline(accept_label="Approve Invoice", decline_label="Dispute Invoice") }}
{{ ak_accept_decline(accept_label="Confirm Order", decline_label="Cancel Order") }}
```

### Rendered HTML
```html
<div class="ak-actions">
  <button type="button" class="ak-accept-btn" data-action="Accepted">Approve Invoice</button>
  <button type="button" class="ak-decline-btn" data-action="Declined">Dispute Invoice</button>
</div>
```

### Response Types
- Clicking Accept sets `response_type = "Accepted"` on the AK Document Response
- Clicking Decline sets `response_type = "Declined"`

---

## ak_submit_button

Renders a single Submit button. Use for forms and data collection where Accept/Decline doesn't apply.

### Signature
```python
ak_submit_button(label="Submit")
```

### Parameters
| Parameter | Type | Default | Description |
|---|---|---|---|
| `label` | str | `"Submit"` | Button text |

### Usage
```html
{{ ak_submit_button() }}
{{ ak_submit_button(label="Submit Feedback") }}
{{ ak_submit_button(label="Complete Registration") }}
```

### Rendered HTML
```html
<div class="ak-actions">
  <button type="button" class="ak-submit-btn" data-action="Submitted">Submit Feedback</button>
</div>
```

### Response Type
- Clicking Submit sets `response_type = "Submitted"` on the AK Document Response

---

## Combining Helpers

You can mix and match helpers freely within a template:

```html
<div class="ak-document">
  <div class="ak-header">
    <h1>Order Confirmation — {{ doc.name }}</h1>
  </div>

  <!-- Read-only document details -->
  <div class="ak-section">
    {{ ak_input("customer_name", label="Customer", value=doc.customer_name, editable=False) }}
    {{ ak_input("order_total", label="Order Total", value=format_currency(doc.grand_total), editable=False) }}
  </div>

  <!-- Items table -->
  {{ ak_items_table(doc) }}

  <!-- Editable fields for recipient -->
  <div class="ak-section">
    <h3>Your Response</h3>
    {{ ak_date("preferred_delivery", label="Preferred Delivery Date", mandatory=True) }}
    {{ ak_select("shipping_method", label="Shipping Method", options=["Standard", "Express", "Overnight"], mandatory=True) }}
    {{ ak_textarea("delivery_notes", label="Delivery Instructions") }}
    {{ ak_checkbox("agree_terms", label="I agree to the terms and conditions") }}
  </div>

  {{ ak_accept_decline(accept_label="Confirm Order", decline_label="Cancel Order") }}
</div>
```
