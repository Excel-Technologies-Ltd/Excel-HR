// Copyright (c) 2026, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Employee Leave Analysis"] = {
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
      fieldname: "employee",
      label: __("Employee"),
      fieldtype: "MultiSelectList",
      get_data: function (txt) {
        var company = frappe.query_report.get_filter_value("company");
        if (!company) {
          return Promise.resolve([]);
        }

        let filters = { company: company };
        if (txt) {
          filters["employee_name"] = ["like", `%${txt}%`];
        }

        return frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Employee",
            filters: filters,
            fields: ["name", "employee_name"],
            limit_page_length: 0,
          },
        }).then((r) => {
          let employees = r.message || [];
          return employees.map((emp) => ({
            value: emp.name,
            label: `${emp.name}`,
            description: emp.employee_name,
          }));
        });
      },
    },
    {
      fieldname: "department",
      label: __("Department"),
      fieldtype: "Link",
      options: "Department",
      get_query: () => {
        var company = frappe.query_report.get_filter_value("company");
        return {
          filters: {
            company: company,
          },
        };
      },
      default: "",
    },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    {
      fieldname: "summarized_view",
      label: __("Summarized View"),
      fieldtype: "Check",
      default: 0,
    },
    {
      fieldname: "is_active",
      label: __("Is Active Employees"),
      fieldtype: "Check",
      default: 1,
    },
    {
      fieldname: "show_abbr",
      label: __("Show Abbr Of Leaves"),
      fieldtype: "Check",
      default: 0,
    },
  ],
  onload: function (report) {
    if (!report.get_filter_value("department")) {
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Employee",
          fieldname: ["department"],
          filters: { user_id: frappe.session.user },
        },
        callback: function (r) {
          if (r.message && r.message.department) {
            report.set_filter_value("department", r.message.department);
          }
        },
      });
    }

    return frappe.call({
      method:
        "hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet.get_attendance_years",
      callback: function (r) {
        var year_filter = report.get_filter("year");
        year_filter.df.options = r.message;
        year_filter.df.default = r.message.split("\n")[0];
        year_filter.refresh();
        year_filter.set_input(year_filter.df.default);
      },
    });
  },
  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    const summarized_view = frappe.query_report.get_filter_value("summarized_view");

    if (!summarized_view && column.colIndex > 1 && value) {
      value = "<span style='color:#318AD8'>" + value + "</span>";
    }

    return value;
  },
};
