// Copyright (c) 2024, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Employee Monthly Attendance Summary"] = {
	"filters": [
		{
			fieldname: "employee",
			label: __("Employee"),
			fieldtype: "Link",
			options: 'Employee',
			
		  },
		{
			"fieldname": "month",
			"label": __("Month"),
			"fieldtype": "Select",
			"reqd": 1 ,
			"options": [
				{ "value": 1, "label": __("Jan") },
				{ "value": 2, "label": __("Feb") },
				{ "value": 3, "label": __("Mar") },
				{ "value": 4, "label": __("Apr") },
				{ "value": 5, "label": __("May") },
				{ "value": 6, "label": __("June") },
				{ "value": 7, "label": __("July") },
				{ "value": 8, "label": __("Aug") },
				{ "value": 9, "label": __("Sep") },
				{ "value": 10, "label": __("Oct") },
				{ "value": 11, "label": __("Nov") },
				{ "value": 12, "label": __("Dec") },
			],
			"default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1
		},
		{
			fieldname: "year",
			label: __("Year"),
			fieldtype: "Link",
			options: "Fiscal Year",
			reqd: 1,
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today()),
		},
		// {
		// 	fieldname: "is_active",
		// 	label: __("Is Active Employees"),
		// 	fieldtype: "Check",
		// 	default: 1,
		// },
	],
	onload: function () {
    // report.get_filter_value("is_active")
	},
	// Custom print/PDF layout with a smaller font so the monthly report fits
	// on fewer pages instead of using the default print-format size.
	html_format: `
		<style>
			.emas-print-table { font-size: 8px; }
			.emas-print-table th, .emas-print-table td { padding: 2px 4px !important; }
		</style>
		{% if title %}<h4>{{ __(title) }}</h4><hr>{% endif %}
		{% if subtitle %}{{ subtitle }}<hr>{% endif %}
		<table class="table table-bordered emas-print-table">
			<thead>
				<tr>
					<th>#</th>
					{% for col in columns %}
						{% if col.name && col._id !== "_check" %}
							<th>{{ __(col.name) }}</th>
						{% endif %}
					{% endfor %}
				</tr>
			</thead>
			<tbody>
				{% for row in data %}
					<tr>
						<td>{{ row._index + 1 }}</td>
						{% for col in columns %}
							{% if col.name && col._id !== "_check" %}
								{% var value = col.fieldname ? row[col.fieldname] : row[col.id] %}
								<td>
									{{
										col.formatter
											? col.formatter(row._index, col._index, value, col, row, true)
											: col.docfield
												? frappe.format(value, col.docfield)
												: value
									}}
								</td>
							{% endif %}
						{% endfor %}
					</tr>
				{% endfor %}
			</tbody>
		</table>
	`,
};
