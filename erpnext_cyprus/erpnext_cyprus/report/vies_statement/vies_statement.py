# Copyright (c) 2024, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def get_filters(filters):
	company = filters.get("company")
	date_range = filters.get("date_range")
	from_date, to_date = date_range if date_range else (None, None)
	cost_center = filters.get("cost_center")
	return company, from_date, to_date, cost_center

def get_columns():
	columns = [
		{
			"label": _("Sales Invoice"),
			"fieldtype": "Link",
			"fieldname": "name",
			"options": "Sales Invoice",
			"width": 200,
		},
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 300,
		},
		{
			"label": _("Posting Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"label": _("Tax ID"),
			"fieldname": "tax_id",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Amount"),
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Rounded Amount"),
			"fieldname": "rounded_grand_total",
			"fieldtype": "Currency",
			"width": 100
		},
	]
	 
	return columns

def get_vies_entries(company, from_date, to_date, cost_center):
	conditions = [
		"company = %s",
		"posting_date >= %s",
		"posting_date <= %s",
		"status = 'Paid'",
		"docstatus = 1",
		"total_taxes_and_charges = 0",
		"tax_id IS NOT NULL AND tax_id != ''"
	]
	values = [company, from_date, to_date]

	if cost_center:
		conditions.append("cost_center = %s")
		values.append(cost_center)

	query = """
		SELECT name, customer, posting_date, tax_id, grand_total, ROUND(grand_total) as rounded_grand_total
		FROM `tabSales Invoice`
		WHERE {conditions}
	""".format(conditions=" AND ".join(conditions))

	result = frappe.db.sql(query, values, as_dict=True)
	return result

def execute(filters=None):
	columns = get_columns()
	company, from_date, to_date, cost_center = get_filters(filters)
	data = []

	data = get_vies_entries(company, from_date, to_date, cost_center)

	return columns, data
