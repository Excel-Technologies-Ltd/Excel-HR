// Extend the template used by the existing Leave Application client script.
// Keep this in Excel HR so HRMS upgrades do not overwrite the column.
frappe.templates["leave_application_dashboard"] = `
{% if not jQuery.isEmptyObject(data) %}
<table class="table table-bordered small">
	<thead>
		<tr>
			<th style="width: 14%">{{ __("Leave Type") }}</th>
			<th style="width: 14%" class="text-right">{{ __("Total Allocated Leaves") }}</th>
			<th style="width: 14%" class="text-right">{{ __("Panalized Leaves") }}</th>
			<th style="width: 14%" class="text-right">{{ __("Expired Leaves") }}</th>
			<th style="width: 14%" class="text-right">{{ __("Used Leaves") }}</th>
			<th style="width: 14%" class="text-right">{{ __("Leaves Pending Approval") }}</th>
			<th style="width: 14%" class="text-right">{{ __("Available Leaves") }}</th>
		</tr>
	</thead>
	<tbody>
		{% for(const [key, value] of Object.entries(data)) { %}
			{% let color = cint(value["remaining_leaves"]) > 0 ? "green" : "red" %}
			<tr>
				<td> {%= key %} </td>
				<td class="text-right"> {%= value["total_leaves"] %} </td>
				<td class="text-right"> {%= value["penalized_leaves"] || 0 %} </td>
				<td class="text-right"> {%= value["expired_leaves"] %} </td>
				<td class="text-right"> {%= value["leaves_taken"] %} </td>
				<td class="text-right"> {%= value["leaves_pending_approval"] %} </td>
				<td class="text-right" style="color: {{ color }}"> {%= value["remaining_leaves"] %} </td>
			</tr>
		{% } %}
	</tbody>
</table>
{% else %}
<p style="margin-top: 30px;"> {{ __("No leaves have been allocated.") }} </p>
{% endif %}
`;
delete frappe.template.compiled["leave_application_dashboard"];

// Limit the Leave Attachments table to MAX_LEAVE_ATTACHMENTS rows.
// The same limit is enforced server side in overrides.py.
const MAX_LEAVE_ATTACHMENTS = 5;

function toggle_leave_attachments_add_row(frm) {
	const count = (frm.doc.custom_leave_attachments || []).length;
	const grid = frm.fields_dict.custom_leave_attachments?.grid;
	if (!grid) return;
	grid.cannot_add_rows = count >= MAX_LEAVE_ATTACHMENTS;
	grid.refresh();
}

frappe.ui.form.on("Leave Application", {
	refresh: toggle_leave_attachments_add_row,
});

// Grid add/remove events are triggered on the child doctype, not the parent.
frappe.ui.form.on("Leave Attachments", {
	custom_leave_attachments_add(frm, cdt, cdn) {
		if ((frm.doc.custom_leave_attachments || []).length > MAX_LEAVE_ATTACHMENTS) {
			// Remove after the grid finishes rendering the new row.
			setTimeout(() => {
				frm.fields_dict.custom_leave_attachments.grid.get_row(cdn)?.remove();
				toggle_leave_attachments_add_row(frm);
			});
			frappe.msgprint(__("You cannot add more than {0} Leave Attachments.", [MAX_LEAVE_ATTACHMENTS]));
			return;
		}
		toggle_leave_attachments_add_row(frm);
	},
	custom_leave_attachments_remove: toggle_leave_attachments_add_row,
});
