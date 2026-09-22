# Copyright (c) 2026, Shaid Azmin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArcHRPolicyImpactLog(Document):
	pass


@frappe.whitelist()
def execute_policy_impact():
	"""Manually trigger the Deduction and Reward policy impact schedulers in the background."""
	frappe.only_for("System Manager")

	from excel_hr.policy_impact import (
		process_late_entry_policy_impact,
		process_ontime_reward_policy_impact,
	)

	# Enqueue these to run in the background to avoid request timeouts
	frappe.enqueue(
		"excel_hr.excel_hr.doctype.archr_policy_impact_log.archr_policy_impact_log.run_policy_impact_jobs",
		timeout=3600 # Give it plenty of time for long date ranges
	)

	return "Policy Impact schedulers have been queued and are running in the background."

def run_policy_impact_jobs():
	"""The actual worker function that runs the processing."""
	from excel_hr.policy_impact import (
		process_late_entry_policy_impact,
		process_ontime_reward_policy_impact,
	)
	process_late_entry_policy_impact()
	process_ontime_reward_policy_impact()

