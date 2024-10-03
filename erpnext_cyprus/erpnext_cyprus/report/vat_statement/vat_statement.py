# Copyright (c) 2024, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_filters(filters):
    company = filters.get("company")
    date_range = filters.get("date_range")
    from_date, to_date = date_range if date_range else (None, None)
    cost_center = filters.get("cost_center")
    cyprus_vat_output_account = filters.get("cyprus_vat_output_account")
    cyprus_vat_input_account = filters.get("cyprus_vat_input_account")
    return company, from_date, to_date, cost_center, cyprus_vat_output_account, cyprus_vat_input_account

def get_columns():
	columns = [
		{
			"label": _("Description"),
			"fieldtype": "Data",
			"fieldname": "description",
			"width": 800,
		},
		{
			"label": _("#"),
			"fieldtype": "Data",
			"fieldname": "desc_id",
			"width": 50,
		},
		{
			"label": _("Amount"),
			"fieldtype": "Currency",
			"fieldname": "amount",
			"options": "currency",
			"width": 100,
		}
	]
	 
	return columns

def get_vat_due_on_sales(company, from_date, to_date, cost_center, cyprus_vat_output_account):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"is_cancelled = 0",
		"credit > 0",
		"account = %s",
		"voucher_type != 'Purchase Invoice'"
	]
	values = [company, from_date, to_date, cyprus_vat_output_account]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(credit) as total_credit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_credit = result[0].get('total_credit') if result and result[0].get('total_credit') is not None else 0
	return total_credit

def get_vat_due_on_acquisitions_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"is_cancelled = 0",
		"credit > 0",
		"account = %s",
		"voucher_type = 'Purchase Invoice'"
	]
	values = [company, from_date, to_date, cyprus_vat_output_account]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(credit) as total_credit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_credit = result[0].get('total_credit') if result and result[0].get('total_credit') is not None else 0
	return total_credit

def get_vat_reclaimed_on_purchases(company, from_date, to_date, cost_center, cyprus_vat_input_account):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"is_cancelled = 0",
		"debit > 0",
		"account = %s"
	]
	values = [company, from_date, to_date, cyprus_vat_input_account]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(debit) as total_debit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_debit = result[0].get('total_debit') if result and result[0].get('total_debit') is not None else 0
	return total_debit

def get_total_value_of_sales_excluding_vat(company, from_date, to_date, cost_center):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"docstatus = 1"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(base_net_total) as total_net_amount
		FROM `tabSales Invoice`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_net_amount = result[0].get('total_net_amount') if result and result[0].get('total_net_amount') is not None else 0
	return total_net_amount

def get_total_value_of_purchases_excluding_vat(company, from_date, to_date, cost_center):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"docstatus = 1"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(base_net_total) as total_net_amount
		FROM `tabPurchase Invoice`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_net_amount = result[0].get('total_net_amount') if result and result[0].get('total_net_amount') is not None else 0
	return total_net_amount

def get_total_value_of_services_supplied_to_eu(company, from_date, to_date, cost_center):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"docstatus = 1",
		"total_taxes_and_charges = 0",
		"tax_id IS NOT NULL AND tax_id != ''"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(base_net_total) as total_net_amount
		FROM `tabSales Invoice`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_net_amount = result[0].get('total_net_amount') if result and result[0].get('total_net_amount') is not None else 0
	return total_net_amount

def get_total_value_of_services_received_excluding_vat(company, from_date, to_date, cost_center):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"status NOT IN ('Cancelled', 'Draft', 'Internal Transfer')",
		"docstatus = 1",
		"total_taxes_and_charges = 0",
		"tax_id IS NOT NULL AND tax_id != ''"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT SUM(base_net_total) as total_net_amount
		FROM `tabPurchase Invoice`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_net_amount = result[0].get('total_net_amount') if result and result[0].get('total_net_amount') is not None else 0
	return total_net_amount

def execute(filters=None):
	columns = get_columns()
	company, from_date, to_date, cost_center, cyprus_vat_output_account, cyprus_vat_input_account = get_filters(filters)
	data = []
	
	vat_due_on_sales = get_vat_due_on_sales(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "VAT due in the period on sales and other outputs", "desc_id": "1", "amount": vat_due_on_sales}
	data.append(row)
	
	vat_due_on_acquisitions_eu = get_vat_due_on_acquisitions_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "VAT due in the period on the acquisitions from other EU Members States", "desc_id": "2", "amount": vat_due_on_acquisitions_eu}
	data.append(row)

	total_vat_due = vat_due_on_sales + vat_due_on_acquisitions_eu
	row = {"description": "Total VAT due", "desc_id": "3", "amount": total_vat_due}
	data.append(row)

	vat_reclaimed_on_purchases = get_vat_reclaimed_on_purchases(company, from_date, to_date, cost_center, cyprus_vat_input_account)
	row = {"description": "VAT reclaimed in the period for purchases and other inputs (including acquisitions from EU)", "desc_id": "4", "amount": vat_reclaimed_on_purchases}
	data.append(row)

	net_vat_to_be_paid_or_reclaimed = total_vat_due - vat_reclaimed_on_purchases
	row = {"description": "Net VAT to be paid or reclaimed", "desc_id": "5", "amount": net_vat_to_be_paid_or_reclaimed}
	data.append(row)

	total_value_of_sales_excluding_vat = get_total_value_of_sales_excluding_vat(company, from_date, to_date, cost_center)
	row = {"description": "Total value of sales and other outputs excluding any VAT (including the amounts in boxes 8A, 8B, 9, 10 and 11B)", "desc_id": "6", "amount": total_value_of_sales_excluding_vat}
	data.append(row)

	total_value_of_purchases_excluding_vat = get_total_value_of_purchases_excluding_vat(company, from_date, to_date, cost_center)
	row = {"description": "Total value of purchases and other inputs excluding any VAT (including the amounts in box 11A and 11B)", "desc_id": "7", "amount": total_value_of_purchases_excluding_vat}
	data.append(row)

	total_value_of_supply_of_goods_and_services_to_eu = 0
	row = {"description": "Total value of supply of goods and related services (excluding VAT) to other Member States", "desc_id": "8A", "amount": total_value_of_supply_of_goods_and_services_to_eu}
	data.append(row)

	total_value_of_services_supplied_to_eu = get_total_value_of_services_supplied_to_eu(company, from_date, to_date, cost_center)
	row = {"description": "Total value of services supplied (excluding VAT) to other Member States", "desc_id": "8B", "amount": total_value_of_services_supplied_to_eu}
	data.append(row)

	total_value_of_zero_rated_supplies = 0
	row = {"description": "Total value of outputs on zero-rated supplies (other than those included in box 8A)", "desc_id": "9", "amount": total_value_of_zero_rated_supplies}
	data.append(row)

	total_value_of_out_of_scope_sales = total_value_of_sales_excluding_vat - total_value_of_services_supplied_to_eu
	row = {"description": "Total value of out of scope sales, with right of deduction of input tax (other than those included in box 8B)", "desc_id": "10", "amount": total_value_of_out_of_scope_sales}
	data.append(row)

	total_value_of_acquisitions_from_eu = 0
	row = {"description": "Total value of all acquisitions of goods and related services (excluding any VAT) from other EU member States", "desc_id": "11A", "amount": total_value_of_acquisitions_from_eu}
	data.append(row)

	total_value_of_services_received_excluding_vat = get_total_value_of_services_received_excluding_vat(company, from_date, to_date, cost_center)
	row = {"description": "Total value of all services receiving (excluding any VAT)", "desc_id": "11B", "amount": total_value_of_services_received_excluding_vat}
	data.append(row)

	return columns, data
