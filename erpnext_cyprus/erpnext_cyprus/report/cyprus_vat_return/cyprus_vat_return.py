# Copyright (c) 2023, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext_cyprus.overrides.company import get_eu_countries

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	return [
		{
			"fieldname": "vat_field",
			"label": _("Field"),
			"fieldtype": "Data",
			"width": 120
		},
		{
			"fieldname": "description",
			"label": _("Description"),
			"fieldtype": "Data",
			"width": 400
		},
		{
			"fieldname": "amount",
			"label": _("Amount (EUR)"),
			"fieldtype": "Currency",
			"options": "currency",
			"width": 150
		}
	]

def get_data(filters):
	company = filters.get("company")
	date_range = filters.get("date_range")
	from_date, to_date = date_range if date_range else (None, None)
	output_vat_account = filters.get("output_vat_account")
	input_vat_account = filters.get("input_vat_account")
	
	if not company or not from_date or not to_date or not output_vat_account or not input_vat_account:
		return []
	
	# Initialize VAT return data and diagnostics
	vat_return_data = []
	diagnostics = []
	
	# Add VAT Return fields according to Cyprus tax requirements
	# Box 1: VAT due on sales and other outputs
	output_vat = get_box_1(company, from_date, to_date, output_vat_account)
	vat_return_data.append({
		"vat_field": _("Box 1"),
		"description": _("VAT due on sales and other outputs"),
		"amount": output_vat
	})

	# Box 2: VAT due on acquisitions from EU countries
	box2 = get_box_2(company, from_date, to_date, output_vat_account, input_vat_account)
	vat_return_data.append({
		"vat_field": _("Box 2"),
		"description": _("VAT due on acquisitions from EU countries"),
		"amount": box2["amount"]
	})
	
	# Box 3: Total VAT due (box 1 + box 2)
	total_vat_due = flt(output_vat) + flt(box2["amount"])
	vat_return_data.append({
		"vat_field": _("Box 3"),
		"description": _("Total VAT due (sum of boxes 1 and 2)"),
		"amount": total_vat_due,
		"bold": 1
	})
	
	# Box 4: VAT reclaimed on purchases and other inputs
	box4 = get_box_4(company, from_date, to_date, input_vat_account, output_vat_account)
	vat_return_data.append({
		"vat_field": _("Box 4"),
		"description": _("VAT reclaimed on purchases and other inputs"),
		"amount": box4["amount"]
	})
	
	# Box 5: Net VAT to be paid or reclaimed
	net_vat = flt(total_vat_due) - flt(box4["amount"])
	vat_return_data.append({
		"vat_field": _("Box 5"),
		"description": _("Net VAT to be paid or reclaimed"),
		"amount": net_vat,
		"bold": 1
	})
	
	# Box 6: Total value of sales and other outputs excluding VAT
	total_sales = get_box_6(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 6"),
		"description": _("Total value of sales and other outputs excluding VAT"),
		"amount": total_sales
	})
	
	# Box 7: Total value of purchases and inputs excluding VAT
	total_purchases = get_box_7(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 7"),
		"description": _("Total value of purchases and inputs excluding VAT"),
		"amount": total_purchases
	})
	
	# Box 8A & 8B: EU goods and services supplies
	eu_supplies_goods = get_box_8a(company, from_date, to_date)
	eu_supplies_services = get_box_8b(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 8A"),
		"description": _("Total value of supplies of goods to EU countries"),
		"amount": eu_supplies_goods
	})
	vat_return_data.append({
		"vat_field": _("Box 8B"),
		"description": _("Total value of supplies of services to EU countries"),
		"amount": eu_supplies_services
	})
	
	# Box 9: Total value of exports to non-EU countries
	non_eu_exports = get_box_9(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 9"),
		"description": _("Total value of exports to non-EU countries"),
		"amount": non_eu_exports
	})
	
	# Box 10: Total value of out-of-scope sales
	out_of_scope = get_box_10(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 10"),
		"description": _("Total value of out-of-scope sales"),
		"amount": out_of_scope
	})
	
	# Box 11A & 11B: EU goods and services acquisitions
	eu_acquisitions_goods = get_box_11a(company, from_date, to_date)
	eu_acquisitions_services = get_box_11b(company, from_date, to_date)
	vat_return_data.append({
		"vat_field": _("Box 11A"),
		"description": _("Total value of acquisitions of goods from EU countries"),
		"amount": eu_acquisitions_goods
	})
	vat_return_data.append({
		"vat_field": _("Box 11B"),
		"description": _("Total value of acquisitions of services from EU countries"),
		"amount": eu_acquisitions_services
	})
	
	# Build diagnostics
	eu_acquisitions_total = flt(eu_acquisitions_goods) + flt(eu_acquisitions_services)
	
	# Diagnostic 1: Reverse-charge PI with empty tax rows
	rc_empty_pis = get_reverse_charge_pis_without_tax_rows(company, from_date, to_date)
	if rc_empty_pis:
		diagnostics.append({
			"vat_field": _("⚠"),
			"description": _("{0} Purchase Invoice(s) use Reverse Charge template but have empty tax rows. VAT computed via fallback.").format(rc_empty_pis),
			"amount": 0,
			"italic": 1
		})
	
	# Diagnostic 2: EU supplier PI without supplier_address
	missing_addr_pis = get_eu_pis_without_supplier_address(company, from_date, to_date)
	if missing_addr_pis:
		diagnostics.append({
			"vat_field": _("⚠"),
			"description": _("{0} Purchase Invoice(s) from EU suppliers are missing supplier_address and may be excluded from Box 11A/11B. Review supplier master data.").format(missing_addr_pis),
			"amount": 0,
			"italic": 1
		})
	
	# Diagnostic 3: Box 11A+11B > 0 but Box 2 is 0
	if eu_acquisitions_total > 0 and box2["amount"] == 0:
		diagnostics.append({
			"vat_field": _("⚠"),
			"description": _("EU acquisitions value (Box 11A+11B) is positive but Box 2 reverse-charge VAT is zero. Check tax template configuration and supplier master data."),
			"amount": 0,
			"italic": 1
		})
	
	# Diagnostic 4: Unmarked JE candidates
	unmarked_je_count = get_unmarked_je_count(company, from_date, to_date, output_vat_account, input_vat_account)
	if unmarked_je_count:
		diagnostics.append({
			"vat_field": _("⚠"),
			"description": _("{0} Journal Entry(s) on VAT accounts without VAT-RC-ADJ marker. These are excluded from adjustment totals.").format(unmarked_je_count),
			"amount": 0,
			"italic": 1
		})
	
	# Add source attribution rows
	if box2["from_tax_rows"] or box2["from_fallback"] or box2["from_je"]:
		vat_return_data.append({
			"vat_field": _("Box 2 Details"),
			"description": _("From PI tax rows: {0} | From fallback: {1} | From JE adjustments: {2}").format(
				box2["from_tax_rows"], box2["from_fallback"], box2["from_je"]
			),
			"amount": 0,
			"italic": 1
		})
	
	if box4["from_sales_gl"] or box4["from_purchase_tax_rows"] or box4["from_fallback"] or box4["from_je"]:
		vat_return_data.append({
			"vat_field": _("Box 4 Details"),
			"description": _("From Sales GL: {0} | From PI tax rows: {1} | From fallback: {2} | From JE adjustments: {3}").format(
				box4["from_sales_gl"], box4["from_purchase_tax_rows"], box4["from_fallback"], box4["from_je"]
			),
			"amount": 0,
			"italic": 1
		})
	
	# Append diagnostics at the end
	vat_return_data.extend(diagnostics)
	
	return vat_return_data

def get_box_1(company, from_date, to_date, output_vat_account):
	# Query for VAT due on sales, handling Credit Notes differently
	query1 = """
		SELECT SUM(
			CASE 
				WHEN gle.voucher_subtype = 'Sales Invoice' THEN gle.credit
				WHEN gle.voucher_subtype = 'Credit Note' THEN -gle.debit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Sales Invoice'
	"""
	
	# Build parameters list
	params = [from_date, to_date, company, output_vat_account]
	
	# Execute query
	sales_vat_result = frappe.db.sql(query1, params, as_dict=1)
	sales_vat = flt(sales_vat_result[0].vat_amount) if sales_vat_result and sales_vat_result[0].vat_amount is not None else 0
	
	return sales_vat

def get_box_2(company, from_date, to_date, output_vat_account, input_vat_account=None):
	"""
	Calculate Box 2: VAT due on EU acquisitions (reverse charge).
	
	Three-tier precedence:
	1. Primary: reverse-charge output VAT from PI tax rows (Deduct rows on Output VAT)
	2. Fallback: derived rate x (Box 11A + Box 11B) when PI tax rows are empty
	3. Adjustment: marked Journal Entry deltas on Output VAT account
	
	Returns dict with keys: amount, from_tax_rows, from_fallback, from_je
	"""
	# Tier 1: Get reverse charge output VAT from PI tax rows
	from_tax_rows = get_reverse_charge_tax_amount(company, from_date, to_date, output_vat_account, 'Deduct')
	
	from_fallback = 0
	# Tier 2: If no tax rows found, apply fallback based on EU acquisition values
	if flt(from_tax_rows) == 0:
		eu_goods = get_box_11a(company, from_date, to_date)
		eu_services = get_box_11b(company, from_date, to_date)
		eu_total = flt(eu_goods) + flt(eu_services)
		if eu_total > 0:
			fallback_rate = get_fallback_vat_rate(company)
			from_fallback = flt(eu_total) * fallback_rate / 100.0
	
	# Tier 3: Get marked JE adjustments on output VAT account
	je_debit, je_credit = get_marked_je_adjustments(company, from_date, to_date, output_vat_account)
	from_je = flt(je_credit) - flt(je_debit)  # Credit increases output VAT liability
	
	total = flt(from_tax_rows) + flt(from_fallback) + flt(from_je)
	
	return {
		"amount": total,
		"from_tax_rows": from_tax_rows,
		"from_fallback": from_fallback,
		"from_je": from_je
	}

def get_box_4(company, from_date, to_date, input_vat_account, output_vat_account=None):
	"""
	Calculate Box 4: VAT reclaimed on purchases and other inputs.
	
	Components:
	1. Sales Invoice input VAT from GL (credit note adjustments)
	2. Purchase Invoice input VAT from PI tax rows (Add rows on Input VAT for ALL suppliers)
	   - This single source replaces the old GL-based purchase query to avoid double counting.
	   - It captures both domestic PIs (with VAT) and EU reverse-charge PIs (Add row on Input VAT).
	   - When GL entries exist, they match; when GL entries don't exist (net-zero reverse charge),
	     the PI tax rows still capture the correct amount.
	3. Fallback mirror when both PI tax rows and GL entries are absent
	4. Marked JE adjustments on Input VAT account
	
	Returns dict with keys: amount, from_sales_gl, from_purchase_tax_rows, from_fallback, from_je
	"""
	# Component 1: Sales Invoice input VAT from GL (credit note VAT recovery)
	query1 = """
		SELECT SUM(
			CASE 
				WHEN gle.voucher_subtype = 'Sales Invoice' THEN gle.debit
				WHEN gle.voucher_subtype = 'Credit Note' THEN -gle.credit
				ELSE 0
			END
		) as vat_amount
		FROM `tabGL Entry` gle
		WHERE gle.posting_date BETWEEN %s AND %s
		AND gle.company = %s
		AND gle.account = %s
		AND gle.is_cancelled = 0
		AND gle.docstatus = 1
		AND gle.voucher_type = 'Sales Invoice'
	"""
	
	params1 = [from_date, to_date, company, input_vat_account]
	sales_vat_result = frappe.db.sql(query1, params1, as_dict=1)
	from_sales_gl = flt(sales_vat_result[0].vat_amount) if sales_vat_result and sales_vat_result[0].vat_amount is not None else 0
	
	# Component 2: Purchase Invoice input VAT from PI tax rows (ALL suppliers, no EU filter).
	# This single source replaces the old GL query to avoid double-counting when
	# both GL entries and PI tax rows exist for the same documents.
	from_purchase_tax_rows = get_all_purchase_input_tax_amount(company, from_date, to_date, input_vat_account)
	
	# Component 3: Fallback mirror - when PI tax rows are empty and EU acquisitions exist
	from_fallback = 0
	if flt(from_purchase_tax_rows) == 0:
		eu_goods = get_box_11a(company, from_date, to_date)
		eu_services = get_box_11b(company, from_date, to_date)
		eu_total = flt(eu_goods) + flt(eu_services)
		if eu_total > 0:
			fallback_rate = get_fallback_vat_rate(company)
			from_fallback = flt(eu_total) * fallback_rate / 100.0
	
	# Component 4: Marked JE adjustments on input VAT account
	je_debit, je_credit = get_marked_je_adjustments(company, from_date, to_date, input_vat_account)
	from_je = flt(je_debit) - flt(je_credit)  # Debit increases input VAT asset
	
	total = flt(from_sales_gl) + flt(from_purchase_tax_rows) + flt(from_fallback) + flt(from_je)
	
	return {
		"amount": total,
		"from_sales_gl": from_sales_gl,
		"from_purchase_tax_rows": from_purchase_tax_rows,
		"from_fallback": from_fallback,
		"from_je": from_je
	}

def get_box_6(company, from_date, to_date):
	# Part 1: Get regular sales excluding VAT directly from Sales Invoice table
	sales_query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabSales Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
	"""
	
	# Execute query for sales invoices
	sales_result = frappe.db.sql(sales_query, [from_date, to_date, company], as_dict=1)
	total_sales = flt(sales_result[0].amount) if sales_result and sales_result[0].amount is not None else 0
	
	# Part 2: Include Purchase Invoices with specific tax templates
	# Get company abbreviation to match template names
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	
	# Template patterns to search for
	special_templates = [
		f"Reverse Charge - {company_abbr}"
	]
	
	template_placeholders = ', '.join(['%s'] * len(special_templates))
	
	purchase_query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabPurchase Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND taxes_and_charges IN ({0})
		AND docstatus = 1
	""".format(template_placeholders)
	
	# Execute query for purchase invoices with special templates
	purchase_params = [from_date, to_date, company] + special_templates
	purchase_result = frappe.db.sql(purchase_query, purchase_params, as_dict=1)
	special_purchase_amount = flt(purchase_result[0].amount) if purchase_result and purchase_result[0].amount is not None else 0
	
	# Combine both components
	return total_sales + special_purchase_amount

def get_box_7(company, from_date, to_date):
	# Get total purchases excluding VAT directly from Purchase Invoice table
	purchase_query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabPurchase Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
	"""
	
	# Execute query
	purchase_result = frappe.db.sql(purchase_query, [from_date, to_date, company], as_dict=1)
	total_purchases = flt(purchase_result[0].amount) if purchase_result and purchase_result[0].amount is not None else 0
	
	return total_purchases

def get_box_8a(company, from_date, to_date):
	# Get EU countries list using utility function
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	query = """
		SELECT SUM(sii.base_net_amount) as amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		LEFT JOIN `tabAddress` addr ON si.customer_address = addr.name
		LEFT JOIN `tabItem` item ON sii.item_code = item.name
		WHERE si.posting_date BETWEEN %s AND %s
		AND si.company = %s
		AND si.docstatus = 1
		AND addr.country IN ({0})
		AND (item.custom_is_service IS NULL OR item.custom_is_service = 0)
	""".format(placeholder_list)
	
	# Build parameters list - add EU countries to the parameters
	params = [from_date, to_date, company] + eu_countries
	
	eu_goods = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_box_8b(company, from_date, to_date):
	# Get EU countries list using utility function
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	query = """
		SELECT SUM(sii.base_net_amount) as amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		LEFT JOIN `tabAddress` addr ON si.customer_address = addr.name
		LEFT JOIN `tabItem` item ON sii.item_code = item.name
		WHERE si.posting_date BETWEEN %s AND %s
		AND si.company = %s
		AND si.docstatus = 1
		AND addr.country IN ({0})
		AND item.custom_is_service = 1
	""".format(placeholder_list)
	
	# Build parameters list - add EU countries to the parameters
	params = [from_date, to_date, company] + eu_countries
	
	eu_services = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_services[0].amount) if eu_services and eu_services[0].amount is not None else 0

def get_box_9(company, from_date, to_date):
	# Get EU countries list using utility function
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	query = """
		SELECT SUM(sii.base_net_amount) as amount
		FROM `tabSales Invoice` si
		INNER JOIN `tabSales Invoice Item` sii ON si.name = sii.parent
		LEFT JOIN `tabAddress` addr ON si.customer_address = addr.name
		LEFT JOIN `tabItem` item ON sii.item_code = item.name
		WHERE si.posting_date BETWEEN %s AND %s
		AND si.company = %s
		AND si.docstatus = 1
		AND addr.country != "Cyprus"
		AND addr.country NOT IN ({0})
		AND (item.custom_is_service IS NULL OR item.custom_is_service = 0)
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + eu_countries
	
	non_eu_exports = frappe.db.sql(query, params, as_dict=1)
	
	return flt(non_eu_exports[0].amount) if non_eu_exports and non_eu_exports[0].amount is not None else 0

def get_box_10(company, from_date, to_date):
	# Get company abbreviation to match template names
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	
	# Out of scope template
	out_of_scope_templates = [
		f"Out-of-Scope - {company_abbr}"
	]
	
	# Format for SQL IN clause
	template_placeholders = ', '.join(['%s'] * len(out_of_scope_templates))
	
	query = """
		SELECT SUM(base_net_total) as amount
		FROM `tabSales Invoice`
		WHERE posting_date BETWEEN %s AND %s
		AND company = %s
		AND docstatus = 1
		AND taxes_and_charges IN ({0})
	""".format(template_placeholders)
	
	# Build parameters list
	params = [from_date, to_date, company] + out_of_scope_templates
	
	# Execute query
	out_of_scope = frappe.db.sql(query, params, as_dict=1)
	
	# Return result
	return flt(out_of_scope[0].amount) if out_of_scope and out_of_scope[0].amount is not None else 0

def get_box_11a(company, from_date, to_date):
	# Get EU countries list
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	# Build query for goods (non-services) from EU countries using supplier country
	query = """
		SELECT SUM(pii.base_net_amount) as amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabSupplier` sup ON pi.supplier = sup.name
		LEFT JOIN `tabItem` item ON pii.item_code = item.name
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND sup.country IN ({0})
		AND (item.custom_is_service IS NULL OR item.custom_is_service = 0)
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + eu_countries
	
	eu_goods = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_goods[0].amount) if eu_goods and eu_goods[0].amount is not None else 0

def get_box_11b(company, from_date, to_date):
	# Get EU countries list
	eu_countries = get_eu_countries()
	
	# Format for SQL IN clause
	placeholder_list = ', '.join(['%s'] * len(eu_countries))
	
	# Build query for services from EU countries using supplier country
	query = """
		SELECT SUM(pii.base_net_amount) as amount
		FROM `tabPurchase Invoice` pi
		INNER JOIN `tabPurchase Invoice Item` pii ON pi.name = pii.parent
		LEFT JOIN `tabSupplier` sup ON pi.supplier = sup.name
		LEFT JOIN `tabItem` item ON pii.item_code = item.name
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND sup.country IN ({0})
		AND item.custom_is_service = 1
	""".format(placeholder_list)
	
	# Build parameters list
	params = [from_date, to_date, company] + eu_countries
	
	eu_services = frappe.db.sql(query, params, as_dict=1)
	
	return flt(eu_services[0].amount) if eu_services and eu_services[0].amount is not None else 0

def get_all_purchase_input_tax_amount(company, from_date, to_date, input_vat_account):
	"""
	Get total input VAT from ALL Purchase Invoice tax rows (no EU filter).
	
	This replaces the old GL-based purchase query to avoid double-counting.
	Captures Add rows on Input VAT for all PIs — both domestic and EU.
	Debit notes have negative base_tax_amount and are handled correctly.
	
	Parameters:
	- company (str): Company to filter
	- from_date, to_date (date): Reporting period
	- input_vat_account (str): The Input VAT account
	
	Returns:
	- float: Total input VAT amount from all PI tax rows
	"""
	query = """
		SELECT SUM(ptc.base_tax_amount) as vat_amount
		FROM `tabPurchase Taxes and Charges` ptc
		INNER JOIN `tabPurchase Invoice` pi ON ptc.parent = pi.name
			AND ptc.parenttype = 'Purchase Invoice'
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND ptc.account_head = %s
		AND ptc.add_deduct_tax = 'Add'
	"""
	
	params = [from_date, to_date, company, input_vat_account]
	result = frappe.db.sql(query, params, as_dict=1)
	return flt(result[0].vat_amount) if result and result[0].vat_amount is not None else 0


def get_reverse_charge_tax_amount(company, from_date, to_date, vat_account, add_deduct_type):
	"""
	Get reverse-charge VAT amount from Purchase Invoice tax rows.
	
	Returns raw base_tax_amount for the given account and add/deduct type.
	No sign negation is applied (unlike total-tax calculation which negates Deduct rows),
	because Box 2 and Box 4 need the actual VAT amount per account.
	Debit notes naturally have negative base_tax_amount and are preserved as-is.
	
	Parameters:
	- company (str): Company to filter
	- from_date, to_date (date): Reporting period
	- vat_account (str): The VAT account to filter (Output or Input)
	- add_deduct_type (str): 'Add' or 'Deduct'
	
	Returns:
	- float: Total VAT amount from PI tax rows
	"""
	eu_countries = get_eu_countries()
	if not eu_countries:
		return 0
	
	placeholders = ', '.join(['%s'] * len(eu_countries))
	
	# Return raw base_tax_amount — no sign negation.
	# Deduct rows represent output VAT (positive for Box 2, negative for debit notes).
	# Add rows represent input VAT (positive for Box 4, negative for debit notes).
	query = f"""
		SELECT SUM(ptc.base_tax_amount) as vat_amount
		FROM `tabPurchase Taxes and Charges` ptc
		INNER JOIN `tabPurchase Invoice` pi ON ptc.parent = pi.name
			AND ptc.parenttype = 'Purchase Invoice'
		LEFT JOIN `tabSupplier` sup ON pi.supplier = sup.name
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND sup.country IN ({placeholders})
		AND ptc.account_head = %s
		AND ptc.add_deduct_tax = %s
	"""
	
	params = [from_date, to_date, company] + eu_countries + [vat_account, add_deduct_type]
	result = frappe.db.sql(query, params, as_dict=1)
	return flt(result[0].vat_amount) if result and result[0].vat_amount is not None else 0


def get_marked_je_adjustments(company, from_date, to_date, vat_account):
	"""
	Get VAT adjustment amounts from marked Journal Entries.
	
	Only includes Journal Entries where the Remark field contains the marker prefix.
	Returns separate debit and credit totals for the caller to apply sign logic.
	
	Parameters:
	- company (str): Company to filter
	- from_date, to_date (date): Reporting period
	- vat_account (str): The VAT account to filter
	
	Returns:
	- tuple: (total_debit, total_credit)
	"""
	marker = 'VAT-RC-ADJ:%'
	query = """
		SELECT SUM(ja.debit) as total_debit, SUM(ja.credit) as total_credit
		FROM `tabJournal Entry Account` ja
		INNER JOIN `tabJournal Entry` je ON ja.parent = je.name
		WHERE je.posting_date BETWEEN %s AND %s
		AND je.company = %s
		AND je.docstatus = 1
		AND ja.account = %s
		AND je.remark LIKE %s
	"""
	params = [from_date, to_date, company, vat_account, marker]
	result = frappe.db.sql(query, params, as_dict=1)
	
	if not result:
		return 0, 0
	
	return flt(result[0].total_debit), flt(result[0].total_credit)


def get_fallback_vat_rate(company):
	"""
	Resolve the reverse-charge VAT rate for fallback calculation.
	
	Resolution order:
	1. Derive from the company's Reverse Charge Purchase Taxes and Charges template
	2. Default to Cyprus standard rate (19%)
	
	Parameters:
	- company (str): Company to look up
	
	Returns:
	- float: VAT rate as percentage (e.g., 19.0 for 19%)
	"""
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	
	# Look for standard reverse-charge template names
	template_names = [
		f"Reverse Charge Services - {company_abbr}",
		f"Reverse Charge - {company_abbr}"
	]
	
	for template_name in template_names:
		rate = frappe.db.get_value(
			"Purchase Taxes and Charges",
			{
				"parent": template_name,
				"add_deduct_tax": "Deduct",
				"parenttype": "Purchase Taxes and Charges Template"
			},
			"rate"
		)
		if rate:
			return flt(rate)
	
	# Default: Cyprus standard VAT rate
	return 19.0


def get_reverse_charge_pis_without_tax_rows(company, from_date, to_date):
	"""
	Count Purchase Invoices that use a Reverse Charge template but have no tax rows.
	
	Parameters:
	- company (str): Company to filter
	- from_date, to_date (date): Reporting period
	
	Returns:
	- int: Count of affected Purchase Invoices
	"""
	company_abbr = frappe.db.get_value("Company", company, "abbr")
	
	template_names = [
		f"Reverse Charge Services - {company_abbr}",
		f"Reverse Charge - {company_abbr}"
	]
	
	placeholders = ', '.join(['%s'] * len(template_names))
	
	query = f"""
		SELECT COUNT(DISTINCT pi.name) as cnt
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabPurchase Taxes and Charges` ptc 
			ON ptc.parent = pi.name AND ptc.parenttype = 'Purchase Invoice'
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND pi.taxes_and_charges IN ({placeholders})
		AND ptc.name IS NULL
	"""
	
	params = [from_date, to_date, company] + template_names
	result = frappe.db.sql(query, params, as_dict=1)
	return flt(result[0].cnt) if result else 0


def get_eu_pis_without_supplier_address(company, from_date, to_date):
	"""
	Count Purchase Invoices from EU suppliers that lack a supplier_address.
	These PIs are excluded from Box 11A/11B and may cause understated fallback.
	
	Parameters:
	- company (str): Company to filter
	- from_date, to_date (date): Reporting period
	
	Returns:
	- int: Count of affected Purchase Invoices
	"""
	eu_countries = get_eu_countries()
	if not eu_countries:
		return 0
	
	placeholders = ', '.join(['%s'] * len(eu_countries))
	
	query = f"""
		SELECT COUNT(DISTINCT pi.name) as cnt
		FROM `tabPurchase Invoice` pi
		LEFT JOIN `tabSupplier` sup ON pi.supplier = sup.name
		LEFT JOIN `tabAddress` addr ON pi.supplier_address = addr.name
		WHERE pi.posting_date BETWEEN %s AND %s
		AND pi.company = %s
		AND pi.docstatus = 1
		AND (
			(pi.supplier_address IS NULL OR pi.supplier_address = '')
			AND sup.country IN ({placeholders})
		)
	"""
	
	params = [from_date, to_date, company] + eu_countries
	result = frappe.db.sql(query, params, as_dict=1)
	return flt(result[0].cnt) if result else 0


def get_unmarked_je_count(company, from_date, to_date, output_vat_account, input_vat_account):
	"""
	Count Journal Entries on VAT accounts that do NOT have the VAT-RC-ADJ marker.
	These are excluded from adjustment totals and should be reviewed.
	
	Parameters:
	- company (str): Company to filter
	- from_date, to_date (date): Reporting period
	- output_vat_account (str): Output VAT account
	- input_vat_account (str): Input VAT account
	
	Returns:
	- int: Count of unmarked Journal Entries on VAT accounts
	"""
	query = """
		SELECT COUNT(DISTINCT je.name) as cnt
		FROM `tabJournal Entry` je
		INNER JOIN `tabJournal Entry Account` ja ON ja.parent = je.name
		WHERE je.posting_date BETWEEN %s AND %s
		AND je.company = %s
		AND je.docstatus = 1
		AND ja.account IN (%s, %s)
		AND (je.remark IS NULL OR je.remark NOT LIKE %s)
	"""
	params = [from_date, to_date, company, output_vat_account, input_vat_account, 'VAT-RC-ADJ:%']
	result = frappe.db.sql(query, params, as_dict=1)
	return flt(result[0].cnt) if result else 0


def get_vat_accounts_from_filter(company, vat_account):
	"""
	Get all tax accounts that are children of the selected vat_account
	and have account_type = 'Tax'
	
	Parameters:
	- company (str): Company for which to fetch accounts
	- vat_account (str): Parent VAT account selected by user
	
	Returns:
	- list: List of account names
	"""
	accounts = []
	
	# Check if selected account itself has account_type = 'Tax'
	account_type = frappe.db.get_value("Account", vat_account, "account_type")
	is_group = frappe.db.get_value("Account", vat_account, "is_group")
	
	if account_type == "Tax":
		accounts.append(vat_account)
	
	# If the selected account is a group account, get its children with account_type = 'Tax'
	if is_group:
		children = frappe.db.sql("""
			SELECT name
			FROM `tabAccount`
			WHERE parent_account = %s
			AND company = %s
			AND account_type = 'Tax'
		""", (vat_account, company), as_dict=1)
		
		# Add all child tax accounts to the list
		for child in children:
			accounts.append(child.name)
	
	return accounts
