# AK Document Designer — Template Examples

Complete, copy-paste-ready template examples. Each example shows the `template_html`, recommended field definitions, and configuration.

---

## Example 1: Sales Invoice with Accept/Decline

**Use case:** Share an invoice with a customer for approval. They can specify a payment date and add comments.

**Reference DocType:** Sales Invoice
**Mode:** Document mode (share existing invoice)

### Template Settings
- Show Accept/Decline: Yes
- Lock After Submission: Yes
- Expires In Days: 14

### Interactive Fields (Child Table)

| Field Name | Label | Type | Existing | Editable | Mandatory |
|---|---|---|---|---|---|
| payment_date | Preferred Payment Date | Date | No | Yes | Yes |
| comments | Comments | Text | No | Yes | No |

### Template HTML

```html
<div class="ak-document">
  <div class="ak-header">
    <table class="ak-two-col">
      <tr>
        <td>
          <h1 style="font-size: 28px; color: #1f2937; margin-bottom: 4px;">INVOICE</h1>
          <p style="font-size: 16px; color: #6b7280;">{{ doc.name }}</p>
        </td>
        <td style="text-align: right;">
          <p><strong>{{ doc.company }}</strong></p>
          <p style="font-size: 13px; color: #6b7280;">Date: {{ doc.posting_date }}</p>
          <p style="font-size: 13px; color: #6b7280;">Due: {{ doc.due_date }}</p>
        </td>
      </tr>
    </table>
  </div>

  <table class="ak-two-col">
    <tr>
      <td>
        <h4 style="color: #6b7280; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Bill To</h4>
        <p><strong>{{ doc.customer_name }}</strong></p>
        <p style="font-size: 13px; color: #4b5563;">{{ doc.address_display or "" }}</p>
      </td>
      <td>
        <h4 style="color: #6b7280; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em;">Invoice Details</h4>
        <p style="font-size: 13px;"><strong>Status:</strong> {{ doc.status }}</p>
        <p style="font-size: 13px;"><strong>Currency:</strong> {{ doc.currency }}</p>
        {% if doc.po_no %}
        <p style="font-size: 13px;"><strong>PO Number:</strong> {{ doc.po_no }}</p>
        {% endif %}
      </td>
    </tr>
  </table>

  {{ ak_items_table(doc, columns=["item_name", "qty", "rate", "amount"]) }}

  {% if doc.discount_amount %}
  <div class="ak-section" style="text-align: right;">
    <p>Subtotal: {{ format_currency(doc.net_total) }}</p>
    <p>Discount: -{{ format_currency(doc.discount_amount) }}</p>
    <p><strong style="font-size: 18px;">Grand Total: {{ format_currency(doc.grand_total) }}</strong></p>
  </div>
  {% endif %}

  {% if doc.terms %}
  <div class="ak-section">
    <h3>Terms & Conditions</h3>
    <div style="font-size: 13px; color: #4b5563;">{{ doc.terms }}</div>
  </div>
  {% endif %}

  <div class="ak-section">
    <h3>Your Response</h3>
    {{ ak_date("payment_date", label="Preferred Payment Date", mandatory=True) }}
    {{ ak_textarea("comments", label="Comments or Questions", rows=3) }}
  </div>

  {{ ak_accept_decline(accept_label="Approve Invoice", decline_label="Dispute Invoice") }}
</div>
```

### Email Subject
```
Invoice {{ doc.name }} from {{ doc.company }} — Please Review
```

### Email Body HTML
```html
<p>Dear {{ doc.customer_name }},</p>
<p>Please find attached invoice <strong>{{ doc.name }}</strong> for <strong>{{ format_currency(doc.grand_total) }}</strong>.</p>
<p>Due date: <strong>{{ doc.due_date }}</strong></p>
<p><a href="{{ share_url }}" style="display: inline-block; padding: 12px 24px; background: #4f46e5; color: #fff; text-decoration: none; border-radius: 6px;">Review and Respond</a></p>
<p style="font-size: 13px; color: #6b7280;">This link expires in {{ share.expires_at }}.</p>
<p>Thank you,<br>{{ doc.company }}</p>
```

---

## Example 2: Quotation with Editable Delivery Date

**Use case:** Send a quotation to a customer. They can choose a delivery date and confirm their address.

**Reference DocType:** Quotation
**Mode:** Document mode

### Template Settings
- Show Accept/Decline: Yes
- Lock After Submission: Yes
- Expires In Days: 7

### Interactive Fields (Child Table)

| Field Name | Label | Type | Existing | Editable | Mandatory | Column |
|---|---|---|---|---|---|---|
| customer_name | Customer | Data | Yes | No | No | Left |
| contact_email | Contact Email | Data | Yes | Yes | Yes | Right |
| delivery_date | Expected Delivery | Date | No | Yes | Yes | Left |
| shipping_method | Shipping | Select | No | Yes | Yes | Right |

**Options for shipping_method:** Standard Shipping\nExpress Shipping\nOvernight\nLocal Pickup

### Template HTML

```html
<div class="ak-document">
  <div class="ak-header">
    <h1>Quotation {{ doc.name }}</h1>
    <p style="color: #6b7280;">Valid until: {{ doc.valid_till or "Not specified" }}</p>
  </div>

  <div class="ak-section">
    <h3>Prepared For</h3>
    <p><strong>{{ doc.customer_name }}</strong></p>
    {% if doc.contact_display %}
    <p>{{ doc.contact_display }}</p>
    {% endif %}
  </div>

  {{ ak_items_table(doc, columns=["item_name", "qty", "rate", "amount"]) }}

  <div class="ak-section" style="text-align: right; font-size: 16px;">
    <p><strong>Total: {{ format_currency(doc.grand_total) }}</strong></p>
  </div>

  {% if doc.terms %}
  <div class="ak-section">
    <h3>Terms</h3>
    <p style="font-size: 13px;">{{ doc.terms }}</p>
  </div>
  {% endif %}

  <div class="ak-section">
    <h3>Please Confirm</h3>
    {{ ak_field_table(columns=2) }}
  </div>

  {{ ak_accept_decline(accept_label="Accept Quotation", decline_label="Decline") }}
</div>
```

---

## Example 3: Contact Update Form (Public Form)

**Use case:** A generic link anyone can use to update their contact information. Creates a new Contact record.

**Reference DocType:** Contact
**Mode:** Public Form (`is_public_form = 1`)

### Template Settings
- Is Public Form: Yes
- Show Accept/Decline: No
- Lock After Submission: Yes
- Expires In Days: 30
- Success Message: "Thank you! Your contact information has been received."

### Interactive Fields (Child Table)

| Field Name | Label | Type | Existing | Editable | Mandatory | Column |
|---|---|---|---|---|---|---|
| first_name | First Name | Data | Yes | Yes | Yes | Left |
| last_name | Last Name | Data | Yes | Yes | No | Right |
| email_id | Email | Data | Yes | Yes | Yes | Left |
| phone | Phone | Data | Yes | Yes | No | Right |
| company_name | Company | Data | Yes | Yes | No | Full Width |

### Template HTML

```html
<div class="ak-document">
  <div class="ak-header" style="text-align: center; border-bottom: none;">
    <h1>Contact Information</h1>
    <p style="color: #6b7280;">Please fill in your details below</p>
  </div>

  <div class="ak-section">
    {{ ak_field_table(columns=2) }}
  </div>

  <div class="ak-section">
    <h3>Additional Information</h3>
    {{ ak_textarea("notes", label="How can we help you?", rows=3, placeholder="Tell us about your inquiry...") }}
    {{ ak_select("source", label="How did you hear about us?", options=["Web Search", "Social Media", "Referral", "Trade Show", "Other"]) }}
  </div>

  {{ ak_submit_button(label="Submit Contact Information") }}
</div>
```

---

## Example 4: Customer Feedback Form

**Use case:** Collect feedback after a service interaction. Shows order details as read-only, collects rating and comments.

**Reference DocType:** Sales Order
**Mode:** Document mode

### Template Settings
- Show Accept/Decline: No
- Lock After Submission: Yes
- Expires In Days: 30
- Success Message: "Thank you for your feedback! We appreciate your time."

### Interactive Fields (Child Table)

| Field Name | Label | Type | Existing | Editable | Mandatory |
|---|---|---|---|---|---|
| satisfaction | Satisfaction Level | Select | No | Yes | Yes |
| recommend | Would Recommend | Select | No | Yes | Yes |
| feedback | Detailed Feedback | Text | No | Yes | No |
| follow_up_ok | OK to Follow Up | Check | No | Yes | No |

**Options for satisfaction:** Very Satisfied\nSatisfied\nNeutral\nDissatisfied\nVery Dissatisfied
**Options for recommend:** Definitely\nProbably\nNot Sure\nProbably Not\nDefinitely Not

### Template HTML

```html
<div class="ak-document">
  <div class="ak-header" style="text-align: center; border-bottom: none;">
    <h1>We'd Love Your Feedback</h1>
    <p style="color: #6b7280;">Regarding Order {{ doc.name }}</p>
  </div>

  <div class="ak-section" style="background: #f9fafb; border-radius: 8px; padding: 20px;">
    <h4 style="color: #6b7280; margin-bottom: 8px;">Order Summary</h4>
    <p><strong>{{ doc.customer_name }}</strong></p>
    <p style="font-size: 13px;">Order Date: {{ doc.transaction_date }}</p>
    <p style="font-size: 13px;">Total: {{ format_currency(doc.grand_total) }}</p>
    <p style="font-size: 13px;">Items: {{ doc.items | length }} item(s)</p>
  </div>

  <div class="ak-section">
    <h3>Your Feedback</h3>

    {{ ak_select("satisfaction", label="How satisfied were you with your experience?",
       options=["Very Satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very Dissatisfied"],
       mandatory=True) }}

    {{ ak_select("recommend", label="Would you recommend us to others?",
       options=["Definitely", "Probably", "Not Sure", "Probably Not", "Definitely Not"],
       mandatory=True) }}

    {{ ak_textarea("feedback", label="Any additional comments?",
       rows=4, placeholder="Tell us what went well or what we could improve...") }}

    {{ ak_checkbox("follow_up_ok", label="It's OK to contact me about my feedback") }}
  </div>

  {{ ak_submit_button(label="Submit Feedback") }}
</div>
```

---

## Example 5: Purchase Order Confirmation

**Use case:** Send a PO to a supplier for confirmation. Supplier can confirm delivery date and add notes.

**Reference DocType:** Purchase Order
**Mode:** Document mode

### Template Settings
- Show Accept/Decline: Yes
- Lock After Submission: Yes
- Expires In Days: 7
- Track Opens: Yes

### Interactive Fields (Child Table)

| Field Name | Label | Type | Existing | Editable | Mandatory |
|---|---|---|---|---|---|
| schedule_date | Confirmed Delivery Date | Date | Yes | Yes | Yes |
| supplier_notes | Supplier Notes | Text | No | Yes | No |

### Template HTML

```html
<div class="ak-document">
  <div class="ak-header">
    <table class="ak-two-col">
      <tr>
        <td>
          <h1 style="margin-bottom: 4px;">Purchase Order</h1>
          <p style="font-size: 18px; color: #4f46e5; font-weight: 600;">{{ doc.name }}</p>
        </td>
        <td style="text-align: right;">
          <p style="font-size: 13px;">Date: {{ doc.transaction_date }}</p>
          <p style="font-size: 13px;">Required By: {{ doc.schedule_date }}</p>
        </td>
      </tr>
    </table>
  </div>

  <table class="ak-two-col">
    <tr>
      <td>
        <h4 style="color: #6b7280; font-size: 12px; text-transform: uppercase;">From</h4>
        <p><strong>{{ doc.company }}</strong></p>
      </td>
      <td>
        <h4 style="color: #6b7280; font-size: 12px; text-transform: uppercase;">To (Supplier)</h4>
        <p><strong>{{ doc.supplier_name }}</strong></p>
        {% if doc.supplier_address %}
        <p style="font-size: 13px;">{{ doc.supplier_address }}</p>
        {% endif %}
      </td>
    </tr>
  </table>

  {{ ak_items_table(doc, columns=["item_name", "qty", "rate", "amount"]) }}

  <div class="ak-section" style="text-align: right;">
    <p style="font-size: 18px;"><strong>Total: {{ format_currency(doc.grand_total) }}</strong></p>
  </div>

  {% if doc.terms %}
  <div class="ak-section">
    <h3>Terms & Conditions</h3>
    <div style="font-size: 13px; color: #4b5563;">{{ doc.terms }}</div>
  </div>
  {% endif %}

  <div class="ak-section">
    <h3>Supplier Response</h3>
    <p style="font-size: 13px; color: #6b7280; margin-bottom: 12px;">
      Please confirm the delivery date and add any notes.
    </p>
    {{ ak_date("schedule_date", label="Confirmed Delivery Date", value=doc.schedule_date, mandatory=True) }}
    {{ ak_textarea("supplier_notes", label="Notes", rows=3, placeholder="Any notes about this order...") }}
  </div>

  {{ ak_accept_decline(accept_label="Confirm Order", decline_label="Cannot Fulfill") }}
</div>
```

---

## Template Patterns Quick Reference

### Read-only document display (no interaction)
```html
<div class="ak-document">
  <div class="ak-header">
    <h1>{{ doc.name }}</h1>
  </div>
  <div class="ak-section">
    <p>{{ doc.description }}</p>
  </div>
  {{ ak_items_table(doc) }}
  {{ ak_submit_button(label="Acknowledge Receipt") }}
</div>
```

### Pure data collection form (public form)
```html
<div class="ak-document">
  <div class="ak-header" style="text-align: center;">
    <h1>Registration Form</h1>
  </div>
  {{ ak_field_table(columns=2) }}
  {{ ak_submit_button(label="Register") }}
</div>
```

### Document with conditional fields
```html
<div class="ak-document">
  {{ ak_items_table(doc) }}
  {% if doc.grand_total > 10000 %}
    <div class="ak-notice">Large orders require a PO number.</div>
    {{ ak_input("po_number", label="PO Number", mandatory=True) }}
  {% endif %}
  {{ ak_accept_decline() }}
</div>
```

### Multi-section document with page breaks
```html
<div class="ak-document">
  <div class="ak-section">
    <h2>Part 1: Overview</h2>
    <!-- content -->
  </div>
  <div class="ak-page-break"></div>
  <div class="ak-section">
    <h2>Part 2: Details</h2>
    <!-- content -->
  </div>
  <div class="ak-page-break"></div>
  <div class="ak-section">
    <h2>Part 3: Agreement</h2>
    {{ ak_checkbox("agree", label="I agree to all terms above") }}
    {{ ak_accept_decline() }}
  </div>
</div>
```
