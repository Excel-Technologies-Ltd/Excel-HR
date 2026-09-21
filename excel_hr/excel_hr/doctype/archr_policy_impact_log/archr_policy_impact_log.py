# Copyright (c) 2026, Shaid Azmin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArcHRPolicyImpactLog(Document):
	pass


@frappe.whitelist()
def execute_policy_impact():
	"""Manually force-run the Deduction and Reward policy impact schedulers."""
	frappe.only_for("System Manager")

	from excel_hr.policy_impact import (
		process_late_entry_policy_impact,
		process_ontime_reward_policy_impact,
	)

	process_late_entry_policy_impact()
	process_ontime_reward_policy_impact()

	return "ArcHR Policy Impact schedulers executed successfully."
