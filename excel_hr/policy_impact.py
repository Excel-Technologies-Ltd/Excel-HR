# Copyright (c) 2026, Shaid Azmin and contributors
# For license information, please see license.txt

"""Cron-scheduled (01:00 daily) processing of the ArcHR attendance policy
impacts. Runs at 1 AM rather than right after midnight because Attendance
for a day isn't created until 11:59 PM that same day -- by 1 AM the
previous day's Attendance is reliably in place.

Only Attendance on or after ArcHR Settings.start_date ("Start Date") is ever
considered, and only for employees whose Status is "Active" and whose
"Attendance Policy Applied?" flag is checked.

Late Entry (Deduction)
----------------------
For every ArcHR Settings.late_entry_cycle_days Attendance records in a
calendar month submitted with Late Entry = 1 (excluding "On Leave" days),
the employee's Annual Leave allocation is reduced by one day, capped at
ArcHR Settings.max_annual_leave_deductions_per_year days deducted per
year. Once that cap is hit, or once the employee's current Annual Leave
allocation is already at zero, the same threshold instead logs a pending
Salary deduction, since there's no more leave to take from.

The cycle behaves as a batch threshold: with a cycle of 5, every complete
block of 5 late entries within the month yields one deduction, while any
leftover entries that don't complete a further block are exempted for that
month. Each resulting "ArcHR Policy Impact Log" entry records the From Date
and To Date spanning that specific block of late entries.

The month-to-date window this job evaluates always ends yesterday, not
today: since it runs at 1 AM, today's Attendance doesn't exist yet, so
counting through "today" would be a no-op most of the time and would
silently truncate the month on the 1st of a new month.

On-Time (Reward)
----------------
Once a calendar month is complete, any employee whose Attendance records
that month (excluding "On Leave") were all on time (no Late Entry) is
granted one Reward Leave day, capped at
ArcHR Settings.max_reward_leaves_per_year reward days a year. Once that
cap is hit, the same monthly 100%-on-time result instead logs a pending
Salary incentive (one day's basic salary) rather than more leave.

Each Reward entry records the judged month in "For Month". When that month
is December -- the last month of the year -- the Reward entry is still
created but no Reward Leave allocation is granted for it, since the yearly
cycle resets at the start of the next year.

Every threshold crossing creates exactly one "ArcHR Policy Impact Log"
entry, backdated (via its Created On) to a date inside the period it was
earned in -- not left at "now" -- so the dedup lookups these jobs run
against their own log history stay correct regardless of what day the job
actually executes on.
"""

import calendar
from datetime import date, timedelta

import frappe
from frappe.utils import cint, flt, getdate


def get_policy_impact_settings():
	return frappe.get_cached_doc("ArcHR Settings")


def get_policy_start_date(settings):
	"""Earliest Attendance date the policy considers, or None if unset."""
	return getdate(settings.start_date) if settings.start_date else None


# ---------------------------------------------------------------------------
# Late Entry -> Annual Leave deduction
# ---------------------------------------------------------------------------

def process_late_entry_policy_impact():
	settings = get_policy_impact_settings()
	if settings.disabled_policy_impact:
		return

	cycle_days = cint(settings.late_entry_cycle_days)
	if cycle_days < 1:
		return

	# Evaluate month-to-date through yesterday -- today's Attendance isn't
	# created yet (it lands at 11:59 PM), and on the 1st of a month this
	# also correctly rolls month_start back to the prior month so its last
	# day still gets counted instead of being cut off.
	reference_date = getdate() - timedelta(days=1)
	month_start = reference_date.replace(day=1)

	# Attendance before the configured Start Date is ignored entirely.
	policy_start = get_policy_start_date(settings)
	window_start = max(month_start, policy_start) if policy_start else month_start
	if window_start > reference_date:
		return

	rows = frappe.db.sql(
		"""
		SELECT a.employee, a.attendance_date
		FROM `tabAttendance` a
		INNER JOIN `tabEmployee` e ON e.name = a.employee
		WHERE a.docstatus = 1
		  AND a.late_entry = 1
		  AND a.status != 'On Leave'
		  AND e.status = 'Active'
		  AND e.custom_attendance_policy_applied = 1
		  AND a.attendance_date BETWEEN %(start)s AND %(end)s
		ORDER BY a.employee, a.attendance_date
		""",
		{"start": window_start, "end": reference_date},
		as_dict=True,
	)

	late_dates_by_employee = {}
	for row in rows:
		late_dates_by_employee.setdefault(row.employee, []).append(row.attendance_date)

	for employee, late_dates in late_dates_by_employee.items():
		due_cycles = len(late_dates) // cycle_days
		if due_cycles < 1:
			continue

		applied_cycles = frappe.db.count(
			"ArcHR Policy Impact Log",
			{
				"employee": employee,
				"criteria": "Deduction",
				"created_on": ["between", [f"{month_start} 00:00:00", f"{reference_date} 23:59:59"]],
			},
		)

		for cycle_index in range(applied_cycles, due_cycles):
			block = late_dates[cycle_index * cycle_days : (cycle_index + 1) * cycle_days]
			apply_late_entry_cycle(
				employee,
				settings,
				created_on=reference_date,
				from_date=block[0],
				to_date=block[-1],
			)


def apply_late_entry_cycle(employee: str, settings=None, created_on=None, from_date=None, to_date=None):
	settings = settings or get_policy_impact_settings()
	max_deductions = cint(settings.max_annual_leave_deductions_per_year)

	reference_date = created_on or getdate()
	year_start = date(reference_date.year, 1, 1)
	year_end = date(reference_date.year, 12, 31)

	leave_deductions_this_year = frappe.db.count(
		"ArcHR Policy Impact Log",
		{
			"employee": employee,
			"criteria": "Deduction",
			"type": "Leaves",
			"status": "Applied",
			"created_on": ["between", [f"{year_start} 00:00:00", f"{year_end} 23:59:59"]],
		},
	)

	allocation = get_active_leave_allocation(employee, "Annual Leave")
	remaining_days = allocation.total_leaves_allocated if allocation else 0

	if leave_deductions_this_year >= max_deductions or not remaining_days:
		create_policy_impact_log(
			employee,
			criteria="Deduction",
			impact_type="Salary",
			status="Pending",
			created_on=created_on,
			from_date=from_date,
			to_date=to_date,
		)
		return

	adjust_leave_allocation(allocation, -1)
	create_policy_impact_log(
		employee,
		criteria="Deduction",
		impact_type="Leaves",
		status="Applied",
		created_on=created_on,
		from_date=from_date,
		to_date=to_date,
	)


# ---------------------------------------------------------------------------
# On-Time month -> Reward Leave grant
# ---------------------------------------------------------------------------

def process_ontime_reward_policy_impact():
	settings = get_policy_impact_settings()
	if settings.disabled_policy_impact:
		return

	# A month can only be judged "complete" once it's over, so this always
	# looks at the last full calendar month relative to today -- unaffected
	# by the 11:59 PM Attendance creation time, since by any day of the
	# following month that month's Attendance is long since finalized.
	today = getdate()
	previous_month_end = today.replace(day=1) - timedelta(days=1)
	previous_month_start = previous_month_end.replace(day=1)

	# Months entirely before the configured Start Date aren't judged.
	policy_start = get_policy_start_date(settings)
	if policy_start and previous_month_end < policy_start:
		return

	attendance_summary = frappe.db.sql(
		"""
		SELECT a.employee,
		       COUNT(*) AS total_count,
		       SUM(CASE WHEN a.late_entry = 1 THEN 1 ELSE 0 END) AS late_count
		FROM `tabAttendance` a
		INNER JOIN `tabEmployee` e ON e.name = a.employee
		WHERE a.docstatus = 1
		  AND a.status != 'On Leave'
		  AND e.status = 'Active'
		  AND e.custom_attendance_policy_applied = 1
		  AND a.attendance_date BETWEEN %(start)s AND %(end)s
		GROUP BY a.employee
		""",
		{"start": previous_month_start, "end": previous_month_end},
		as_dict=True,
	)

	for_month = calendar.month_name[previous_month_start.month]
	# December is the last month of the year: the Reward entry is created,
	# but no Reward Leave allocation is granted for it.
	is_december = previous_month_start.month == 12

	for row in attendance_summary:
		if not row.total_count or row.late_count:
			continue

		already_processed = frappe.db.exists(
			"ArcHR Policy Impact Log",
			{
				"employee": row.employee,
				"criteria": "Reward",
				"created_on": [
					"between",
					[f"{previous_month_start} 00:00:00", f"{previous_month_end} 23:59:59"],
				],
			},
		)
		if already_processed:
			continue

		apply_ontime_reward_cycle(
			row.employee,
			settings,
			created_on=previous_month_end,
			for_month=for_month,
			grant_allocation=not is_december,
		)


def apply_ontime_reward_cycle(
	employee: str, settings=None, created_on=None, for_month=None, grant_allocation=True
):
	settings = settings or get_policy_impact_settings()
	max_reward_leaves = cint(settings.max_reward_leaves_per_year)

	reference_date = created_on or getdate()
	year_start = date(reference_date.year, 1, 1)
	year_end = date(reference_date.year, 12, 31)

	reward_leaves_this_year = frappe.db.count(
		"ArcHR Policy Impact Log",
		{
			"employee": employee,
			"criteria": "Reward",
			"type": "Leaves",
			"status": "Applied",
			"created_on": ["between", [f"{year_start} 00:00:00", f"{year_end} 23:59:59"]],
		},
	)

	if grant_allocation and reward_leaves_this_year >= max_reward_leaves:
		create_policy_impact_log(
			employee,
			criteria="Reward",
			impact_type="Salary",
			status="Pending",
			created_on=created_on,
			for_month=for_month,
		)
		return

	if grant_allocation:
		grant_reward_leave(employee)

	create_policy_impact_log(
		employee,
		criteria="Reward",
		impact_type="Leaves",
		status="Applied",
		created_on=created_on,
		for_month=for_month,
	)


def grant_reward_leave(employee: str):
	"""Creates the employee's yearly Reward Leave allocation if none exists
	yet, otherwise grants one more day on the existing one."""
	allocation = get_active_leave_allocation(employee, "Reward Leave")
	if allocation:
		adjust_leave_allocation(allocation, 1)
		return

	year = getdate().year
	company = frappe.db.get_value("Employee", employee, "company")

	allocation = frappe.get_doc(
		{
			"doctype": "Leave Allocation",
			"employee": employee,
			"leave_type": "Reward Leave",
			"company": company,
			"from_date": date(year, 1, 1),
			"to_date": date(year, 12, 31),
			"new_leaves_allocated": 1,
			"carry_forward": 0,
		}
	)
	allocation.flags.ignore_permissions = True
	allocation.insert()
	allocation.submit()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def get_active_leave_allocation(employee: str, leave_type: str):
	today = getdate()
	name = frappe.db.get_value(
		"Leave Allocation",
		{
			"employee": employee,
			"leave_type": leave_type,
			"docstatus": 1,
			"from_date": ["<=", today],
			"to_date": [">=", today],
		},
		"name",
		order_by="to_date desc",
	)
	return frappe.get_doc("Leave Allocation", name) if name else None


def adjust_leave_allocation(allocation, delta: float):
	"""Grants (delta > 0) or takes back (delta < 0) leave days on an already
	submitted Leave Allocation via its "New Leaves Allocated" field, which
	Leave Allocation's own on_update_after_submit hook turns into a matching
	Leave Ledger Entry and a recalculated Total Leaves Allocated -- the
	officially supported way to adjust a submitted allocation, so the change
	is reflected everywhere HRMS computes leave balance from the ledger, not
	just in this app's own reading of the allocation's total field.
	"""
	allocation.flags.ignore_permissions = True
	allocation.new_leaves_allocated = max(flt(allocation.new_leaves_allocated) + delta, 0)
	allocation.save()


def create_policy_impact_log(
	employee: str,
	criteria: str,
	impact_type: str,
	status: str,
	adjustment: int = 1,
	created_on=None,
	from_date=None,
	to_date=None,
	for_month=None,
):
	doc = frappe.get_doc(
		{
			"doctype": "ArcHR Policy Impact Log",
			"criteria": criteria,
			"type": impact_type,
			"status": status,
			"adjustment": adjustment,
			"employee": employee,
		}
	)
	if created_on:
		doc.created_on = created_on
	if from_date:
		doc.from_date = from_date
	if to_date:
		doc.to_date = to_date
	if for_month:
		doc.for_month = for_month
	doc.insert(ignore_permissions=True)