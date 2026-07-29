// Copyright (c) 2026, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Monthly Attendance Matrix"] = {
  filters: [
    {
      fieldname: "date_range",
      label: __("Date Range"),
      fieldtype: "Date Range",
      reqd: 1,
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
      fieldname: "custom_job_location",
      label: __("Job Location"),
      fieldtype: "Link",
      options: "Branch",
    },
    {
      fieldname: "excel_department",
      label: __("Parent Department"),
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
      fieldname: "excel_section",
      label: __("Section"),
      fieldtype: "Link",
      options: "Department",
      get_query: function () {
        var main_department = frappe.query_report.get_filter_value("excel_department");
        if (main_department) {
          return {
            filters: {
              parent_department: main_department,
            },
          };
        } else {
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
        var main_department = frappe.query_report.get_filter_value("excel_section");
        if (main_department) {
          return {
            filters: {
              parent_department: main_department,
            },
          };
        } else {
          return {};
        }
      },
    },
  ],
  formatter: function (value, row, column, data, default_formatter) {
    // "ID" column: show the raw Employee ID, not the title field
    // (employee_name) that Frappe's Link formatter auto-resolves to.
    if (column.fieldname === "employee") {
      return data.employee;
    }

    value = default_formatter(value, row, column, data);

    const colors = {
      present: "green",
      present_percent: "green",
      wfh: "green",
      wfh_percent: "green",
      leave: "#318AD8",
      leave_percent: "#318AD8",
      leave_application: "#318AD8",
      leave_application_percent: "#318AD8",
      weekly_off: "brown",
      weekly_off_percent: "brown",
      holiday: "brown",
      holiday_percent: "brown",
      ar_application: "orange",
      ar_application_percent: "orange",
      absent: "red",
      absent_percent: "red",
    };

    if (colors[column.fieldname]) {
      value = "<span style='color:" + colors[column.fieldname] + "'>" + value + "</span>";
    } else if (column.fieldname === "total") {
      value = "<strong>" + value + "</strong>";
    }

    return value;
  },
  // This report has 24 columns, so the table is usually wider than the
  // viewport. A plain mouse wheel only scrolls the container vertically by
  // default (horizontal scroll needs Shift+wheel or dragging the thin
  // scrollbar), which makes the columns past the visible edge easy to miss
  // entirely. Translate vertical wheel input into horizontal scroll here.
  after_datatable_render: function (datatable) {
    const scrollable = datatable.wrapper.querySelector(".dt-scrollable");
    if (!scrollable || scrollable.dataset.wheelScrollBound) return;
    scrollable.dataset.wheelScrollBound = "1";

    scrollable.addEventListener(
      "wheel",
      function (e) {
        if (e.deltaY !== 0 && scrollable.scrollWidth > scrollable.clientWidth) {
          e.preventDefault();
          scrollable.scrollLeft += e.deltaY;
        }
      },
      { passive: false }
    );
  },
};
