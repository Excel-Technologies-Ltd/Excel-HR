// For license information, please see license.txt
/* eslint-disable */

// set_options for excel_subsection

// excel job location

// Copyright (c) 2023, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Employee Leave Balance Summary"] = {
  filters: [
    //   {
    // 	fieldname: "date",
    // 	label: __("Date"),
    // 	fieldtype: "Date",
    // 	reqd: 1,
    // 	default: frappe.datetime.year_end(),
    // 	readonly:1
    //   },
    //   {
    // 	"fieldname": "month",
    // 	"label": __("Month"),
    // 	"fieldtype": "Select",
    // 	"reqd": 1 ,
    // 	"options": [
    // 		{ "value": 1, "label": __("Jan") },
    // 		{ "value": 2, "label": __("Feb") },
    // 		{ "value": 3, "label": __("Mar") },
    // 		{ "value": 4, "label": __("Apr") },
    // 		{ "value": 5, "label": __("May") },
    // 		{ "value": 6, "label": __("June") },
    // 		{ "value": 7, "label": __("July") },
    // 		{ "value": 8, "label": __("Aug") },
    // 		{ "value": 9, "label": __("Sep") },
    // 		{ "value": 10, "label": __("Oct") },
    // 		{ "value": 11, "label": __("Nov") },
    // 		{ "value": 12, "label": __("Dec") },
    // 	],
    // 	"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
    // },
    {
      fieldname: "year",
      label: __("Year"),
      fieldtype: "Select",
      default: "2024",
      options: [
        { value: 2023, label: __("2023") },
        { value: 2024, label: __("2024") },
        { value: 2025, label: __("2025") },
        { value: 2026, label: __("2026") },
        { value: 2027, label: __("2027") },
      ],
    },

    //   {
    // 	fieldname: "date_range",
    // 	label: __("Date Range"),
    // 	fieldtype: "Date Range",
    // 	reqd: 1,
    // 	default: [frappe.datetime.year_start(), frappe.datetime.month_end()],
    //   },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      reqd: 1,
      default: frappe.defaults.get_user_default("Company"),
    },
    // here employee i want multiselect
    {
      fieldname: "employee",
      label: __("Employee"),
      fieldtype: "MultiSelectList",
      get_data: function (txt) {
        return frappe.db.get_link_options("Employee", txt);
      },
    },

    {
      fieldname: "excel_department",
      label: __("Parent Department"),
      fieldtype: "Link",
      options: "Department",
    },

    {
      fieldname: "excel_section",
      label: __("Section"),
      fieldtype: "Link",
      options: "Department",
      get_query: function () {
        var main_department =
          frappe.query_report.get_filter_value("excel_department");
        if (main_department) {
          return {
            filters: {
              parent_department: main_department,
            },
          };
        } else {
          // If the parent value is not selected, show all departments
          return {};
        }
      },
    },

    {
      fieldname: "excel_sub_section",
      label: __("Sub Section"),
      fieldtype: "Link",
      options: "Department",
      get_query: function () {
        var main_department =
          frappe.query_report.get_filter_value("excel_section");
        if (main_department) {
          return {
            filters: {
              parent_department: main_department,
            },
          };
        } else {
          // If the parent value is not selected, show all departments
          return {};
        }
      },
    },
    {
      fieldname: "custom_job_location",
      label: __("Excel Job Location"),
      fieldtype: "Link",
      options: "Branch",
    },
    {
      fieldname: "custom_reporting_location",
      label: __("Excel Reporting Location"),
      fieldtype: "Link",
      options: "Branch",
    },
    {
      fieldname: "employee_status",
      label: __("Employee Status"),
      fieldtype: "Select",
      options: [
        "",
        { value: "Active", label: __("Active") },
        { value: "Inactive", label: __("Inactive") },
        { value: "Suspended", label: __("Suspended") },
        { value: "Left", label: __("Left") },
      ],
      default: "Active",
    },
  ],
};
