import frappe
from frappe.utils import today, getdate, add_days, nowdate, cint, flt


def evaluate_conditions(automation, doc):
	"""Evaluate all conditions for an automation against a document.

	Returns True if:
	- No conditions defined (always run), OR
	- All 'All Conditions' rows pass AND at least one 'Any Conditions' row passes
	"""
	all_conds = automation.all_conditions or []
	any_conds = automation.any_conditions or []

	if not all_conds and not any_conds:
		return True

	# All conditions must pass (AND)
	if all_conds:
		for cond in all_conds:
			if not _evaluate_single(cond, doc):
				return False

	# At least one Any condition must pass (OR)
	if any_conds:
		any_passed = False
		for cond in any_conds:
			if _evaluate_single(cond, doc):
				any_passed = True
				break
		if not any_passed:
			return False

	return True


def _evaluate_single(cond, doc):
	"""Evaluate a single condition row against the document."""
	field = cond.field
	operator = cond.operator
	value = cond.value
	value2 = cond.value2

	doc_value = doc.get(field)
	meta = frappe.get_meta(doc.doctype)
	df = meta.get_field(field)
	fieldtype = df.fieldtype if df else "Data"

	# ── Change detection operators ──
	if operator in ("has changed", "has changed to", "has changed from"):
		return _eval_change(operator, field, value, doc)

	# ── Empty checks ──
	if operator == "is empty":
		return not doc_value
	if operator == "is not empty":
		return bool(doc_value)

	# ── Date-specific operators ──
	if fieldtype in ("Date", "Datetime"):
		return _eval_date(operator, doc_value, value, value2)

	# ── Numeric operators ──
	if fieldtype in ("Int", "Float", "Currency", "Percent"):
		return _eval_numeric(operator, doc_value, value, value2)

	# ── Text/Select/Link operators ──
	return _eval_text(operator, doc_value, value)


def _eval_change(operator, field, value, doc):
	"""Evaluate has changed / has changed to / has changed from."""
	if not hasattr(doc, "_doc_before_save") or not doc._doc_before_save:
		# New document — consider all fields as "changed"
		if operator == "has changed":
			return True
		if operator == "has changed to":
			return str(doc.get(field) or "") == str(value or "")
		return False

	old_val = doc._doc_before_save.get(field)
	new_val = doc.get(field)

	if operator == "has changed":
		return old_val != new_val
	elif operator == "has changed to":
		return old_val != new_val and str(new_val or "") == str(value or "")
	elif operator == "has changed from":
		return old_val != new_val and str(old_val or "") == str(value or "")

	return False


def _eval_date(operator, doc_value, value, value2):
	"""Evaluate date-specific operators."""
	if not doc_value:
		return operator in ("is empty",)

	try:
		doc_date = getdate(doc_value)
	except Exception:
		return False

	today_date = getdate(today())

	if operator in ("is", "="):
		return doc_date == getdate(value)
	elif operator in ("is not", "!="):
		return doc_date != getdate(value)
	elif operator == "before":
		return doc_date < getdate(value)
	elif operator == "after":
		return doc_date > getdate(value)
	elif operator == "between":
		return getdate(value) <= doc_date <= getdate(value2)
	elif operator == "is today":
		return doc_date == today_date
	elif operator == "is tomorrow":
		return doc_date == getdate(add_days(today(), 1))
	elif operator == "is yesterday":
		return doc_date == getdate(add_days(today(), -1))
	elif operator == "less than days ago":
		days = cint(value)
		cutoff = getdate(add_days(today(), -days))
		return doc_date > cutoff
	elif operator == "more than days ago":
		days = cint(value)
		cutoff = getdate(add_days(today(), -days))
		return doc_date < cutoff
	elif operator == "less than days later":
		days = cint(value)
		cutoff = getdate(add_days(today(), days))
		return doc_date < cutoff and doc_date >= today_date
	elif operator == "more than days later":
		days = cint(value)
		cutoff = getdate(add_days(today(), days))
		return doc_date > cutoff

	return False


def _eval_numeric(operator, doc_value, value, value2):
	"""Evaluate numeric operators."""
	doc_val = flt(doc_value)
	cmp_val = flt(value)

	if operator in ("is", "="):
		return doc_val == cmp_val
	elif operator in ("is not", "!="):
		return doc_val != cmp_val
	elif operator == ">":
		return doc_val > cmp_val
	elif operator == "<":
		return doc_val < cmp_val
	elif operator == ">=":
		return doc_val >= cmp_val
	elif operator == "<=":
		return doc_val <= cmp_val
	elif operator == "between":
		return flt(value) <= doc_val <= flt(value2)

	return False


def _eval_text(operator, doc_value, value):
	"""Evaluate text, select, and link operators."""
	doc_str = str(doc_value or "")
	cmp_str = str(value or "")

	if operator == "is":
		return doc_str == cmp_str
	elif operator == "is not":
		return doc_str != cmp_str
	elif operator == "contains":
		return cmp_str.lower() in doc_str.lower()
	elif operator == "does not contain":
		return cmp_str.lower() not in doc_str.lower()
	elif operator == "starts with":
		return doc_str.lower().startswith(cmp_str.lower())
	elif operator == "ends with":
		return doc_str.lower().endswith(cmp_str.lower())

	return False
