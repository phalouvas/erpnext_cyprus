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
            fieldname: "date_range",
            label: __("Date Range"),
            fieldtype: "DateRange",
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
		},
		{
			fieldname: "cyprus_vat_input_account",
			label: __("Cyprus VAT Input Account"),
			fieldtype: "Link",
			options: "Account",
			reqd: 1
		}
	]
};
