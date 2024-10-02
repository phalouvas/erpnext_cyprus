// Copyright (c) 2024, KAINOTOMO PH LTD and contributors
// For license information, please see license.txt

frappe.query_reports["VAT Statement"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1
		},
		{
			fieldname: "cost_center",
			label: __("Cost Center"),
			fieldtype: "Link",
			options: "Cost Center",
			reqd: 0
		},
		{
			fieldname: "cyprus_vat_output_account",
			label: __("Cyprus VAT Output Account"),
			fieldtype: "Link",
			options: "Account",
			reqd: 1
		}
	]
};
