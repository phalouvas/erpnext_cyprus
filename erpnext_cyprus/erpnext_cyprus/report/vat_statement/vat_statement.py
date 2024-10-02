# Copyright (c) 2024, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_filters(filters):
	company = filters.get("company")
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	cost_center = filters.get("cost_center")
	cyprus_vat_output_account = filters.get("cyprus_vat_output_account")
	return company, from_date, to_date, cost_center, cyprus_vat_output_account

def get_columns():
	columns = [
		{
			"label": _("Description"),
			"fieldtype": "Data",
			"fieldname": "description",
			"width": 500,
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
		"voucher_type != 'Purchase Invoice'"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	if cyprus_vat_output_account:
		conditions.append("account = %s")
		values.append(cyprus_vat_output_account)

	query = """
		SELECT SUM(credit) as total_credit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_credit = result[0].get('total_credit') if result else 0
	return total_credit

def get_vat_due_on_acquisitions_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"is_cancelled = 0",
		"credit > 0",
		"voucher_type = 'Purchase Invoice'"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	if cyprus_vat_output_account:
		conditions.append("account = %s")
		values.append(cyprus_vat_output_account)

	query = """
		SELECT SUM(credit) as total_credit
		FROM `tabGL Entry`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	total_credit = result[0].get('total_credit') if result else 0
	return total_credit

def execute(filters=None):
	columns = get_columns()
	company, from_date, to_date, cost_center, cyprus_vat_output_account = get_filters(filters)
	data = []
	
	vat_due_on_sales = get_vat_due_on_sales(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "VAT due in the period on sales and other outputs", "amount": vat_due_on_sales}
	data.append(row)
	
	vat_due_on_acquisitions_eu = get_vat_due_on_acquisitions_eu(company, from_date, to_date, cost_center, cyprus_vat_output_account)
	row = {"description": "VAT due in the period on the acquisitions from other EU Members States", "amount": vat_due_on_acquisitions_eu}
	data.append(row)

	total_vat_due = vat_due_on_sales + vat_due_on_acquisitions_eu
	row = {"description": "Total VAT due", "amount": total_vat_due}
	data.append(row)
	
	return columns, data
