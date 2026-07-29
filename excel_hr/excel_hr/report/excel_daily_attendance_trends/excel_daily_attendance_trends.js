// Copyright (c) 2026, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Daily Attendance Trends"] = {
  filters: [
    {
      fieldname: "date_range",
      label: __("Date Range"),
      fieldtype: "Date Range",
      reqd: 1,
      default: "",
    },
  ],
  formatter: function (value, row, column, data, default_formatter) {
    value = default_formatter(value, row, column, data);

    if (column.fieldname === "metric") {
      return "<strong>" + value + "</strong>";
    }

    const colors = {
      P: "green",
      "P%": "green",
      WFH: "green",
      "WFH%": "green",
      L: "#318AD8",
      "L%": "#318AD8",
      "L.App": "#318AD8",
      "L.App%": "#318AD8",
      WO: "brown",
      "WO%": "brown",
      H: "brown",
      "H%": "brown",
      "AR.App": "orange",
      "AR.App%": "orange",
      A: "red",
      "A%": "red",
    };

    const metric = data.metric;
    if (colors[metric]) {
      value = "<span style='color:" + colors[metric] + "'>" + value + "</span>";
    } else if (metric === "Total Count") {
      value = "<strong>" + value + "</strong>";
    }

    return value;
  },
  // This report is intentionally wide (one column per date), so the table
  // is almost always wider than the viewport. A plain mouse wheel only
  // scrolls the container vertically by default (horizontal scroll needs
  // Shift+wheel or dragging the thin scrollbar), which makes the columns
  // past the visible edge easy to miss entirely. Translate vertical wheel
  // input into horizontal scroll on this report's table specifically.
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
