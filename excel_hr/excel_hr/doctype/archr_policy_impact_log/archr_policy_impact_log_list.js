// Copyright (c) 2026, Shaid Azmin and contributors
// For license information, please see license.txt

frappe.listview_settings['ArcHR Policy Impact Log'] = {
	onload: function (listview) {
		if (!frappe.user.has_role('System Manager')) {
			return;
		}

		listview.page.add_inner_button(__('Execute'), function () {
			frappe.confirm(
				__(
					'Are you sure you want to force execute the Deduction and Reward schedulers?'
				),
				function () {
					frappe.call({
						method: 'excel_hr.excel_hr.doctype.archr_policy_impact_log.archr_policy_impact_log.execute_policy_impact',
						callback: function (r) {
							if (r.message) {
								frappe.msgprint({
									message: r.message,
									indicator: 'blue',
									title: __('Background Task Started')
								});
							}
							listview.refresh();
						},
					});
				}
			);
		});
	},
};