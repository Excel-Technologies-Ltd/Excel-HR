// Copyright (c) 2024, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.query_reports["Excel Attendance Sheet"] = {
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
      get_data: function(txt) {
        var company = frappe.query_report.get_filter_value("company");
        if (!company) {
          return Promise.resolve([]);
        }
        
        let filters = {company: company};
        if (txt) {
          filters['employee_name'] = ['like', `%${txt}%`];
        }
        
        return frappe.call({
          method: "frappe.client.get_list",
          args: {
            doctype: "Employee",
            filters: filters,
            fields: ["name", "employee_name"],
            limit_page_length: 0
          }
        }).then(r => {
          let employees = r.message || [];
          return employees.map(emp => ({
            value: emp.name,
            label: `${emp.name}`,
            description: emp.employee_name
          }));
        });
      }
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
    },
    {
      fieldname: "company",
      label: __("Company"),
      fieldtype: "Link",
      options: "Company",
      default: frappe.defaults.get_user_default("Company"),
      reqd: 1,
    },
    // {
    //   fieldname: "group_by",
    //   label: __("Group By"),
    //   fieldtype: "Select",
    //   options: ["", "Branch", "Grade", "Department", "Designation"],
    // },
    {
      fieldname: "summarized_view",
      label: __("Summarized View"),
      fieldtype: "Check",
      Default: 0,
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
    return frappe.call({
      method:
        "hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet.get_attendance_years",
      callback: function (r) {
        var year_filter = frappe.query_report.get_filter("year");
        year_filter.df.options = r.message;
        year_filter.df.default = r.message.split("\n")[0];
        year_filter.refresh();
        year_filter.set_input(year_filter.df.default);
      },
    });
  },
  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);
    const summarized_view =
      frappe.query_report.get_filter_value("summarized_view");
    const group_by = frappe.query_report.get_filter_value("group_by");

    if (group_by && column.colIndex === 1) {
      value = "<strong>" + value + "</strong>";
    }

    if (!summarized_view) {
      if (
        (group_by && column.colIndex > 3) ||
        (!group_by && column.colIndex > 2)
      ) {
        if (value == "P" || value == "WFH")
          value = "<span style='color:green'>" + value + "</span>";
        else if (value == "A")
          value = "<span style='color:red'>" + value + "</span>";
        else if (value == "HD")
          value = "<span style='color:orange'>" + value + "</span>";
        else if (value == "L")
          value = "<span style='color:#318AD8'>" + value + "</span>";
      }
    }

    return value;
  },
};
