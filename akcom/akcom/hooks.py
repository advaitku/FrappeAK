app_name = "akcom"
app_title = "AKCOM"
app_publisher = "AK"
app_description = "Private support ledger and billing tracker"
app_email = "ak@example.com"
app_license = "MIT"

after_install = "akcom.setup.install.after_install"

has_permission = {
	"AKCOM Person": "akcom.akcom.doctype.akcom_person.akcom_person.has_permission",
	"AKCOM Ledger Entry": "akcom.akcom.doctype.akcom_ledger_entry.akcom_ledger_entry.has_permission",
}

permission_query_conditions = {
	"AKCOM Person": "akcom.akcom.doctype.akcom_person.akcom_person.get_permission_query_conditions",
	"AKCOM Ledger Entry": "akcom.akcom.doctype.akcom_ledger_entry.akcom_ledger_entry.get_permission_query_conditions",
}
