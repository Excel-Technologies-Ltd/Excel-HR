// Copyright (c) 2024, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Employees In-Exit Time Report"] = {
	"filters": [
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"reqd": 1,
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
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1,
			"on_change": function() {
				let month = frappe.query_report.get_filter_value("month");
				let year = frappe.query_report.get_filter_value("year");
				let start_date = frappe.datetime.obj_to_str(new Date(year, month - 1, 1));
				let end_date = frappe.datetime.obj_to_str(new Date(year, month, 0)); // Last day of the month
				frappe.query_report.set_filter_value("date_range", [start_date, end_date]);
			}
		},
		{
			"fieldname": "year",
			"label": __("Year"),
			"fieldtype": "Select",
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getFullYear(),
			"options": [
				{ "value": 2023, "label": __("2023") },
				{ "value": 2024, "label": __("2024") },
				{ "value": 2025, "label": __("2025") },
				{ "value": 2026, "label": __("2026") },
				{ "value": 2027, "label": __("2027") },
				{ "value": 2028, "label": __("2028") },
				{ "value": 2029, "label": __("2029") },
			],
			"on_change": function() {
				// Trigger month change to recalculate the date range when year changes
				frappe.query_report.get_filter("month").on_change();
			}
		},
		{
			"fieldname": "date_range",
			"label": __("Date Range"),
			"fieldtype": "Date Range",
			"reqd": 1,
			"default": [frappe.datetime.year_start(), frappe.datetime.month_end()],
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company"),
		},
		{
			"fieldname": "employee",
			"label": __("Employee"),
			"fieldtype": "MultiSelectList",
			"get_data": function(txt) {
				return frappe.db.get_link_options("Employee", txt);
			},
		}
	]
};
