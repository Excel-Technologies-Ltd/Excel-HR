// Copyright (c) 2026, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Attendance Log"] = {
  filters: [
    {
      fieldname: "date_range",
      label: __("Date Range"),
      fieldtype: "Date Range",
      reqd: 1,
      default: [frappe.datetime.get_today(), frappe.datetime.get_today()],
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
      fieldname: "is_active",
      label: __("Is Active Employees"),
      fieldtype: "Check",
      default: 1,
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
  },
  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    if (column.fieldname === "in_status") {
      if (value == "LATE") value = "<span style='color:red'>" + value + "</span>";
      else if (value == "INTIME") value = "<span style='color:green'>" + value + "</span>";
    }

    if (column.fieldname === "out_status") {
      if (value == "Early") value = "<span style='color:red'>" + value + "</span>";
      else if (value == "INTIME") value = "<span style='color:green'>" + value + "</span>";
    }

    if (
      (column.fieldname === "roster_time") &&
      (value == "Holiday" || value == "Weekend")
    ) {
      value = "<span style='color:#318AD8'>" + value + "</span>";
    }

    return value;
  },
};
