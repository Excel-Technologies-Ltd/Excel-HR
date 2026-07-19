// Copyright (c) 2024, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Monthly Attendance Summary"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: 'Employee',
			
		  },
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"reqd": 1 ,
			"options": [
				{ "value": 1, "label": __("Jan") },
				{ "value": 2, "label": __("Feb") },
				{ "value": 3, "label": __("Mar") },
				{ "value": 4, "label": __("Apr") },
				{ "value": 5, "label": __("May") },
				{ "value": 6, "label": __("June") },
				{ "value": 7, "label": __("July") },
				{ "value": 8, "label": __("Aug") },
				{ "value": 9, "label": __("Sep") },
				{ "value": 10, "label": __("Oct") },
				{ "value": 11, "label": __("Nov") },
				{ "value": 12, "label": __("Dec") },
			],
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1,
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
		},
		// {
		// 	fieldname: "is_active",
		// 	label: __("Is Active Employees"),
		// 	fieldtype: "Check",
		// 	default: 1,
		// },
	],
	onload: function () {
    // report.get_filter_value("is_active")
	},
};
