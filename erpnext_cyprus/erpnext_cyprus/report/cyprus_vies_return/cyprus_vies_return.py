# Copyright (c) 2025, KAINOTOMO PH LTD and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt
from erpnext_cyprus.overrides.company import get_eu_countries

def execute(filters=None):
	return get_columns(), get_data(filters)

def get_columns():
	columns = [
		{
			"label": _("Customer"),
			"fieldtype": "Link",
			"fieldname": "customer",
			"options": "Customer",
			"width": 300,
		},
		{
			"label": _("Country"),
			"fieldname": "country",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Tax ID"),
			"fieldname": "tax_id",
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"label": _("Rounded Net Total"),
			"fieldname": "rounded_net_total",
			"fieldtype": "Currency",
			"width": 100
		},
	]
	 
	return columns


def get_data(filters):
	company = filters.get("company")
	date_range = filters.get("date_range")
	from_date, to_date = date_range if date_range else (None, None)
	
	if not company or not from_date or not to_date:
		return []
	
	# Get EU countries except Cyprus
	eu_countries = get_eu_countries()
	
	# Query to get sales invoices grouped by customer
	# Country is derived from the customer_address on the invoice
	customer_totals = frappe.db.sql(
		"""
		SELECT 
			si.customer,
			c.tax_id,
			addr.country,
			SUM(si.net_total) as net_total,
			SUM(ROUND(si.net_total, 0)) as rounded_net_total
		FROM 
			`tabSales Invoice` si
		INNER JOIN 
			`tabCustomer` c ON si.customer = c.name
		LEFT JOIN
			`tabAddress` addr ON addr.name = si.customer_address
		WHERE 
			si.docstatus = 1
			AND si.company = %s
			AND si.posting_date BETWEEN %s AND %s
			AND si.total_taxes_and_charges = 0
			AND c.tax_id IS NOT NULL AND c.tax_id != ''
			AND addr.country IN %s
		GROUP BY
			si.customer, c.tax_id, addr.country
		ORDER BY 
			addr.country, si.customer
		""",
		(company, from_date, to_date, tuple(eu_countries)),
		as_dict=1,
	)
	
	return customer_totals
