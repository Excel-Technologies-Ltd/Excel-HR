# Copyright (c) 2026, Shaid Azmin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ArcHRPolicyImpactLog(Document):
	def on_update(self):
		if self.has_value_changed("status"):
			# old_status = self.get_value_before_save("status")
			old_status = self.get_doc_before_save()
			
			if self.type == "Leaves":
				if old_status == "Applied" and self.status == "Rejected":
					self.rollback_leave_allocation()
				elif old_status == "Pending" and self.status == "Applied":
					self.apply_leave_allocation()

	def apply_leave_allocation(self):
		from excel_hr.policy_impact import get_active_leave_allocation, adjust_leave_allocation, grant_reward_leave

		if self.criteria == "Reward":
			# Rule: December doesn't get allocation
			if self.to_date and self.to_date.month == 12:
				return
			grant_reward_leave(self.employee, to_date=self.to_date, adjustment=self.adjustment)
		
		elif self.criteria == "Deduction":
			allocation = get_active_leave_allocation(self.employee, "Annual Leave", date_for_allocation=self.to_date)
			if allocation:
				adjust_leave_allocation(allocation, -self.adjustment)

	def rollback_leave_allocation(self):
		from excel_hr.policy_impact import get_active_leave_allocation, adjust_leave_allocation

		if self.criteria == "Reward":
			# Rule: December didn't get allocation, so don't rollback
			if self.to_date and self.to_date.month == 12:
				return
			
			allocation = get_active_leave_allocation(self.employee, "Reward Leave", date_for_allocation=self.to_date)
			if allocation:
				adjust_leave_allocation(allocation, -self.adjustment)

		elif self.criteria == "Deduction":
			allocation = get_active_leave_allocation(self.employee, "Annual Leave", date_for_allocation=self.to_date)
			if allocation:
				adjust_leave_allocation(allocation, self.adjustment)


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

