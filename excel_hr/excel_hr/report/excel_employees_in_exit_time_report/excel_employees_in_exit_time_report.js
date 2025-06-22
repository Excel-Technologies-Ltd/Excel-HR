// Copyright (c) 2024, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Employees In-Exit Time Report"] = {
  filters: [
    {
      fieldname: "month",
      label: __("Month"),
      fieldtype: "Select",
      reqd: 1,
      options: [
        { value: 1, label: __("Jan") },
        { value: 2, label: __("Feb") },
        { value: 3, label: __("Mar") },
        { value: 4, label: __("Apr") },
        { value: 5, label: __("May") },
        { value: 6, label: __("June") },
        { value: 7, label: __("July") },
        { value: 8, label: __("Aug") },
        { value: 9, label: __("Sep") },
        { value: 10, label: __("Oct") },
        { value: 11, label: __("Nov") },
        { value: 12, label: __("Dec") },
      ],
      default:
        frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1,
      on_change: function () {
        let month = frappe.query_report.get_filter_value("month");
        let year = frappe.query_report.get_filter_value("year");
        let start_date = frappe.datetime.obj_to_str(
          new Date(year, month - 1, 1)
        );
        let end_date = frappe.datetime.obj_to_str(new Date(year, month, 0)); // Last day of the month
        frappe.query_report.set_filter_value("date_range", [
          start_date,
          end_date,
        ]);
      },
    },
    {
      fieldname: "year",
      label: __("Year"),
      fieldtype: "Link",
      options: "Fiscal Year",
      reqd: 1,
      default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
    },
    {
      fieldname: "date_range",
      label: __("Date Range"),
      fieldtype: "Date Range",
      reqd: 1,
      default: [frappe.datetime.month_start(), frappe.datetime.month_end()],
      on_change: function () {
        const date_range = frappe.query_report.get_filter_value("date_range");

        if (date_range && date_range[0] && date_range[1]) {
          const start_date = new Date(date_range[0]);
          const end_date = new Date(date_range[1]);

          // Get the month and year from the start date
          const month = start_date.getMonth(); // 0 = January, 1 = February, etc.
          const year = start_date.getFullYear();

          // Set max days in the month
          let maxDays;
          if (month === 1) {
            // February
            // Check for leap year
            maxDays =
              year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
                ? 29
                : 28;
          } else if ([3, 5, 8, 10].includes(month)) {
            // April, June, September, November
            maxDays = 30;
          } else {
            maxDays = 31;
          }

          // Calculate difference in time (milliseconds)
          const diffTime = Math.abs(end_date - start_date);

          // Convert difference from milliseconds to days
          const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

          // Validate if the difference exceeds the allowed days for the month
          if (diffDays > maxDays - 1) {
            frappe.msgprint(
              __(
                "The date range cannot exceed " +
                  maxDays +
                  " days for the selected month."
              ),
              __("Validation Error")
            );
            frappe.query_report.set_filter_value("date_range", null);
          }
        }
      },
    },

    // {
    // 	"fieldname": "company",
    // 	"label": __("Company"),
    // 	"fieldtype": "Link",
    // 	"options": "Company",
    // 	"reqd": 1,
    // 	"default": frappe.defaults.get_user_default("Company"),
    // },,
    {
      fieldname: "employee",
      label: __("Employee"),
      fieldtype: "MultiSelectList",
      get_data: function (txt) {
        return frappe.db.get_link_options("Employee", txt);
      },
      on_change: function () {
        // Trigger month change to recalculate the date range when year changes
        frappe.query_report.set_filter_value("department", "");
      },
      // "default": frappe.defaults.get_user_default("Employee")
    },
    {
      fieldname: "department",
      label: __("Department"),
      fieldtype: "Link",
      options: "Department",
      default: function () {
        // Fetch the current user's department from their Employee record
        let employee = frappe.session.user;
        if (employee) {
          frappe.call({
            method: "frappe.client.get_value",
            args: {
              doctype: "Employee",
              fieldname: "department",
              filters: { user_id: employee },
            },
            callback: function (r) {
              if (r.message) {
                // Return the department value
                frappe.query_report.set_filter_value(
                  "department",
                  r.message.department
                );
                return r.message.department;
              } else {
                // If no department is found, resolve with an empty string
                return "";
              }
            },
          });
        } else {
          // If no employee is linked, return an empty string
          return "";
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
    fieldname: "is_active",
    label: __("Is Active Employees"),
    fieldtype: "Check",
    default: 1,
    },
  ],
  onload: function () {
    report.get_filter_value("is_active")
  },
};

