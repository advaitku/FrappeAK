"""Expression and formula evaluation for field updates.

Supports:
- Simple math: annual_revenue/12, amount * 1.1
- Field references: doc.fieldname
- Date math: today() + 30, doc.due_date + 7
- String functions: concat(firstname, ' ', lastname)
- Conditional: if mailingcountry == 'India' then concat(firstname,' ',lastname)
                else concat(lastname,' ',firstname) end
"""

import frappe
from frappe.utils import today, add_days, now_datetime, getdate, flt, cint


def resolve_value(value_type, update, doc):
	"""Resolve a field update value based on its type."""
	if value_type == "Static Value":
		return update.get("value", "")

	elif value_type == "Today":
		return today()

	elif value_type == "Today + N Days":
		n = cint(update.get("days_offset") or update.get("days", 0))
		return add_days(today(), n)

	elif value_type == "Today - N Days":
		n = cint(update.get("days_offset") or update.get("days", 0))
		return add_days(today(), -n)

	elif value_type == "Use Field":
		source = update.get("source_field") or update.get("value", "")
		return doc.get(source)

	elif value_type == "Current User":
		return frappe.session.user

	elif value_type == "Clear":
		return None

	elif value_type == "Expression":
		return evaluate_expression(update.get("value", ""), doc)

	elif value_type == "Use Function":
		return evaluate_function(update, doc)

	return update.get("value", "")


def evaluate_expression(expr, doc):
	"""Evaluate a formula expression with doc context.

	Supports:
	- annual_revenue/12
	- doc.amount * 1.1
	- if status == 'Open' then 'Active' else 'Inactive' end
	- concat(firstname, ' ', lastname)
	"""
	if not expr or not expr.strip():
		return None

	expr = expr.strip()

	# Handle if/then/else/end
	if expr.lower().startswith("if "):
		return _eval_conditional(expr, doc)

	# Handle function calls
	if "(" in expr and ")" in expr:
		return _eval_with_functions(expr, doc)

	# Simple expression — evaluate with safe_eval
	return _safe_eval(expr, doc)


def _eval_conditional(expr, doc):
	"""Parse and evaluate: if CONDITION then VALUE else VALUE end"""
	lower = expr.lower()

	# Find the positions of then/else/end
	then_pos = lower.find(" then ")
	else_pos = lower.find(" else ")
	end_pos = lower.rfind(" end")

	if then_pos == -1:
		frappe.throw(f"Invalid if/then expression: missing 'then'")

	condition_str = expr[3:then_pos].strip()

	if else_pos != -1 and end_pos != -1:
		then_value = expr[then_pos + 6:else_pos].strip()
		else_value = expr[else_pos + 6:end_pos].strip()
	elif else_pos == -1 and end_pos != -1:
		then_value = expr[then_pos + 6:end_pos].strip()
		else_value = None
	else:
		then_value = expr[then_pos + 6:].strip()
		else_value = None

	# Evaluate condition
	condition_result = _safe_eval(condition_str, doc)

	if condition_result:
		return _eval_with_functions(then_value, doc) if "(" in then_value else _safe_eval(then_value, doc)
	elif else_value is not None:
		return _eval_with_functions(else_value, doc) if "(" in else_value else _safe_eval(else_value, doc)
	return None


def _eval_with_functions(expr, doc):
	"""Evaluate expressions that may contain function calls."""
	# Built-in functions available in expressions
	func_map = {
		"concat": _fn_concat,
		"uppercase": _fn_uppercase,
		"lowercase": _fn_lowercase,
		"trim": _fn_trim,
		"length": _fn_length,
		"round": _fn_round,
		"abs": _fn_abs,
		"today": lambda *args: today(),
		"now": lambda *args: now_datetime(),
	}

	# Build a safe context
	context = _build_context(doc)
	context.update(func_map)

	try:
		return frappe.safe_eval(expr, eval_globals=context, eval_locals={})
	except Exception:
		# Fallback: try string return
		return expr


def _safe_eval(expr, doc):
	"""Safely evaluate a simple expression."""
	context = _build_context(doc)
	try:
		return frappe.safe_eval(expr, eval_globals=context, eval_locals={})
	except Exception:
		# If evaluation fails, return as string
		return expr


def _build_context(doc):
	"""Build the evaluation context dict from a document."""
	context = {}
	# Add all doc fields as top-level variables
	for key in doc.as_dict():
		context[key] = doc.get(key)
	# Also available as doc.fieldname
	context["doc"] = doc
	context["frappe"] = frappe
	context["today"] = today
	context["add_days"] = add_days
	context["now"] = now_datetime
	context["getdate"] = getdate
	context["flt"] = flt
	context["cint"] = cint
	return context


# ── Built-in functions ──

def _fn_concat(*args):
	return "".join(str(a) if a is not None else "" for a in args)


def _fn_uppercase(val):
	return str(val or "").upper()


def _fn_lowercase(val):
	return str(val or "").lower()


def _fn_trim(val):
	return str(val or "").strip()


def _fn_length(val):
	return len(str(val or ""))


def _fn_round(val, digits=0):
	return round(flt(val), cint(digits))


def _fn_abs(val):
	return abs(flt(val))


def evaluate_function(update, doc):
	"""Evaluate a Use Function value type."""
	func_name = update.get("function_name", "")
	value = update.get("value", "")
	source = update.get("source_field", "")

	source_val = doc.get(source) if source else value

	func_map = {
		"concat": _fn_concat,
		"uppercase": _fn_uppercase,
		"lowercase": _fn_lowercase,
		"trim": _fn_trim,
		"length": _fn_length,
		"round": _fn_round,
		"abs": _fn_abs,
		"ceil": lambda v: __import__("math").ceil(flt(v)),
		"floor": lambda v: __import__("math").floor(flt(v)),
	}

	fn = func_map.get(func_name)
	if fn:
		return fn(source_val)

	return source_val
