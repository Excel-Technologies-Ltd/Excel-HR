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
