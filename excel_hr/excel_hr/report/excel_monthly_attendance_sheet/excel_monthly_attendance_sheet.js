frappe.query_reports["Excel Monthly Attendance Sheet"] = {
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
      fieldtype: "Select",
      reqd: 1,
    },

    ,
    // {
    // 	"fieldname": "start_date",
    // 	"label": __("Start Date"),
    // 	"fieldtype": "Date",
    // 	"default":frappe.datetime.month_start()

    // },
    // {
    // 	"fieldname": "end_date",
    // 	"label": __("End Date"),
    // 	"fieldtype": "Date",
    // 	"default":frappe.datetime.month_end()

    // },

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
      options: "Branch"
    },
    // {
    // 	"fieldname":"group_by",
    // 	"label": __("Group By"),
    // 	"fieldtype": "Select",
    // 	"excel_sub_section": ["","Branch","Grade","Department","Designation"]
    // },
    {
      fieldname: "summarized_view",
      label: __("Summarized View"),
      fieldtype: "Check",
      Default: 0,
    },
    {
      fieldname: "show_abbr",
      label: __("Show Abbr Of Attendance"),
      fieldtype: "Check",
      Default: 0,
    },
  ],
  onload: function () {
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
