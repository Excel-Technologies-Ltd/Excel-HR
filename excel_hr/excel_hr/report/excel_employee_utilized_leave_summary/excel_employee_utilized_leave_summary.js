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
      fieldname: "excel_job_location",
      label: __("Excel Job Location"),
      fieldtype: "Select",
      options: [
        "",
        { value: "Head Office", label: "Head Office" },
        { value: "HQ, Baridhara", label: "HQ, Baridhara" },
        { value: "Baridhara Service Point", label: "Baridhara Service Point" },
        { value: "Corporate Office", label: "Corporate Office" },
        { value: "Dhanmondi Warehouse", label: "Dhanmondi Warehouse" },
        { value: "E. Road Zone", label: "E. Road Zone" },
        { value: "Dhanmondi Zone", label: "Dhanmondi Zone" },
        { value: "IDB", label: "IDB" },
        { value: "Multiplan", label: "Multiplan" },
        { value: "Uttara", label: "Uttara" },
        { value: "CTG", label: "CTG" },
        { value: "CTG Corporate", label: "CTG Corporate" },
        { value: "CTG Zone", label: "CTG Zone" },
        {
          value: "Bangabandhu Hi-Tech City",
          label: "Bangabandhu Hi-Tech City",
        },
        { value: "KHULNA", label: "KHULNA" },
        { value: "RAJSHAHI", label: "RAJSHAHI" },
        { value: "SYLHET", label: "SYLHET" },
        { value: "Motijheel Zone", label: "Motijheel Zone" },
        { value: "Gulistan Zone", label: "Gulistan Zone" },
        { value: "Savar Zone", label: "Savar Zone" },
        { value: "Gazipur Zone", label: "Gazipur Zone" },
        { value: "Narayanganj Zone", label: "Narayanganj Zone" },
        { value: "Khulna Zone", label: "Khulna Zone" },
        { value: "Bogura Zone", label: "Bogura Zone" },
        { value: "Sylhet Zone", label: "Sylhet Zone" },
        { value: "Rangpur Zone", label: "Rangpur Zone" },
        { value: "Faridpur Zone", label: "Faridpur Zone" },
        { value: "Rajshahi Zone", label: "Rajshahi Zone" },
        { value: "Mymensingh Zone", label: "Mymensingh Zone" },
        { value: "Feni Zone", label: "Feni Zone" },
        { value: "Barishal Zone", label: "Barishal Zone" },
        { value: "Kusthia Zone", label: "Kusthia Zone" },
        { value: "Dinajpur Zone", label: "Dinajpur Zone" },
        { value: "Noakhali Zone", label: "Noakhali Zone" },
        { value: "Pabna Zone", label: "Pabna Zone" },
        { value: "Tangail Zone", label: "Tangail Zone" },
        { value: "Comilla Zone", label: "Comilla Zone" },
        { value: "CCSP-Multiplan", label: "CCSP-Multiplan" },
        { value: "CSP-Baridhara", label: "CSP-Baridhara" },
        { value: "CSP-Uttara", label: "CSP-Uttara" },
        { value: "CSP-IDB", label: "CSP-IDB" },
        { value: "CSP-Gazipur", label: "CSP-Gazipur" },
        { value: "CSP-Motijheel", label: "CSP-Motijheel" },
        { value: "CSP-Gulistan", label: "CSP-Gulistan" },
        { value: "CSP-Narayanganj", label: "CSP-Narayanganj" },
        { value: "CSP-Savar", label: "CSP-Savar" },
        { value: "CSP-CTG", label: "CSP-CTG" },
        { value: "CSP-Rangpur", label: "CSP-Rangpur" },
        { value: "CSP-Sylhet", label: "CSP-Sylhet" },
        { value: "CSP-Khulna", label: "CSP-Khulna" },
        { value: "CSP-Rajshahi", label: "CSP-Rajshahi" },
        { value: "CSP-Feni", label: "CSP-Feni" },
        { value: "CSP-Mymensingh", label: "CSP-Mymensingh" },
        { value: "CSP-Bogura", label: "CSP-Bogura" },
        { value: "CSP-Barishal", label: __("CSP-Barishal") },
      ],
    },
    {
      fieldname: "excel_reporting_location",
      label: __("Excel Reporting Location"),
      fieldtype: "Select",
      options: [
        "",
        { value: "Head Office", label: "Head Office" },
        { value: "HQ, Baridhara", label: "HQ, Baridhara" },
        { value: "Baridhara Service Point", label: "Baridhara Service Point" },
        { value: "Corporate Office", label: "Corporate Office" },
        { value: "Dhanmondi Warehouse", label: "Dhanmondi Warehouse" },
        { value: "E. Road Zone", label: "E. Road Zone" },
        { value: "Dhanmondi Zone", label: "Dhanmondi Zone" },
        { value: "IDB", label: "IDB" },
        { value: "Multiplan", label: "Multiplan" },
        { value: "Uttara", label: "Uttara" },
        { value: "CTG", label: "CTG" },
        { value: "CTG Corporate", label: "CTG Corporate" },
        { value: "CTG Zone", label: "CTG Zone" },
        {
          value: "Bangabandhu Hi-Tech City",
          label: "Bangabandhu Hi-Tech City",
        },
        { value: "KHULNA", label: "KHULNA" },
        { value: "RAJSHAHI", label: "RAJSHAHI" },
        { value: "SYLHET", label: "SYLHET" },
        { value: "Motijheel Zone", label: "Motijheel Zone" },
        { value: "Gulistan Zone", label: "Gulistan Zone" },
        { value: "Savar Zone", label: "Savar Zone" },
        { value: "Gazipur Zone", label: "Gazipur Zone" },
        { value: "Narayanganj Zone", label: "Narayanganj Zone" },
        { value: "Khulna Zone", label: "Khulna Zone" },
        { value: "Bogura Zone", label: "Bogura Zone" },
        { value: "Sylhet Zone", label: "Sylhet Zone" },
        { value: "Rangpur Zone", label: "Rangpur Zone" },
        { value: "Faridpur Zone", label: "Faridpur Zone" },
        { value: "Rajshahi Zone", label: "Rajshahi Zone" },
        { value: "Mymensingh Zone", label: "Mymensingh Zone" },
        { value: "Feni Zone", label: "Feni Zone" },
        { value: "Barishal Zone", label: "Barishal Zone" },
        { value: "Kusthia Zone", label: "Kusthia Zone" },
        { value: "Dinajpur Zone", label: "Dinajpur Zone" },
        { value: "Noakhali Zone", label: "Noakhali Zone" },
        { value: "Pabna Zone", label: "Pabna Zone" },
        { value: "Tangail Zone", label: "Tangail Zone" },
        { value: "Comilla Zone", label: "Comilla Zone" },
        { value: "CCSP-Multiplan", label: "CCSP-Multiplan" },
        { value: "CSP-Baridhara", label: "CSP-Baridhara" },
        { value: "CSP-Uttara", label: "CSP-Uttara" },
        { value: "CSP-IDB", label: "CSP-IDB" },
        { value: "CSP-Gazipur", label: "CSP-Gazipur" },
        { value: "CSP-Motijheel", label: "CSP-Motijheel" },
        { value: "CSP-Gulistan", label: "CSP-Gulistan" },
        { value: "CSP-Narayanganj", label: "CSP-Narayanganj" },
        { value: "CSP-Savar", label: "CSP-Savar" },
        { value: "CSP-CTG", label: "CSP-CTG" },
        { value: "CSP-Rangpur", label: "CSP-Rangpur" },
        { value: "CSP-Sylhet", label: "CSP-Sylhet" },
        { value: "CSP-Khulna", label: "CSP-Khulna" },
        { value: "CSP-Rajshahi", label: "CSP-Rajshahi" },
        { value: "CSP-Feni", label: "CSP-Feni" },
        { value: "CSP-Mymensingh", label: "CSP-Mymensingh" },
        { value: "CSP-Bogura", label: "CSP-Bogura" },
        { value: "CSP-Barishal", label: __("CSP-Barishal") },
      ],
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
