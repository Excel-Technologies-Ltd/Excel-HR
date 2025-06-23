// For license information, please see license.txt
/* eslint-disable */

// set_options for excel_subsection

// excel job location

// Copyright (c) 2023, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Employee Utilized Leave Summary"] = {
  filters: [
    {
      fieldname: "date_range",
      label: __("Date Range"),
      fieldtype: "Date Range",
      reqd: 1,
      default: [frappe.datetime.year_start(), frappe.datetime.year_end()],
    },
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
      options: "Branch"
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
