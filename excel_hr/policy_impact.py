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
from collections import defaultdict

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

    reference_date = getdate() - timedelta(days=1)
    policy_start = get_policy_start_date(settings)
    window_start = max(date(2000, 1, 1), policy_start) if policy_start else date(2000, 1, 1)

    # Fetch all late entries since Start Date
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

    # Group by employee and month
    late_data = defaultdict(list)
    for row in rows:
        month_key = (row.employee, row.attendance_date.year, row.attendance_date.month)
        late_data[month_key].append(row.attendance_date)

    for (employee, year, month), late_dates in late_data.items():
        due_cycles = len(late_dates) // cycle_days
        if due_cycles < 1:
            continue

        month_start = date(year, month, 1)
        # Find last day of that specific month
        if month == 12:
            month_end = date(year, 12, 31)
        else:
            month_end = date(year, month + 1, 1) - timedelta(days=1)

        applied_cycles = frappe.db.sql("""
            SELECT COUNT(name) FROM `tabArcHR Policy Impact Log`
            WHERE employee = %s AND criteria = 'Deduction'
            AND (
                (to_date IS NOT NULL AND to_date BETWEEN %s AND %s)
                OR
                (to_date IS NULL AND created_on BETWEEN %s AND %s)
            )
        """, (employee, month_start, month_end, f"{month_start} 00:00:00", f"{month_end} 23:59:59"))[0][0]

        for cycle_index in range(applied_cycles, due_cycles):
            block = late_dates[cycle_index * cycle_days : (cycle_index + 1) * cycle_days]
            apply_late_entry_cycle(
                employee,
                settings,
                from_date=block[0],
                to_date=block[-1],
            )

def apply_late_entry_cycle(employee: str, settings=None, from_date=None, to_date=None):
    settings = settings or get_policy_impact_settings()
    max_deductions = cint(settings.max_annual_leave_deductions_per_year)

    reference_date = to_date or getdate()
    year_start = date(reference_date.year, 1, 1)
    year_end = date(reference_date.year, 12, 31)

    leave_deductions_this_year = frappe.db.sql("""
        SELECT COUNT(name) FROM `tabArcHR Policy Impact Log`
        WHERE employee = %s AND criteria = 'Deduction' AND type = 'Leaves' AND status = 'Applied'
        AND (
            (to_date IS NOT NULL AND to_date BETWEEN %s AND %s)
            OR
            (to_date IS NULL AND created_on BETWEEN %s AND %s)
        )
    """, (employee, year_start, year_end, f"{year_start} 00:00:00", f"{year_end} 23:59:59"))[0][0]

    allocation = get_active_leave_allocation(employee, "Annual Leave", date_for_allocation=to_date)
    remaining_days = allocation.total_leaves_allocated if allocation else 0

    created_on = frappe.utils.now()

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

    if allocation:
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

    today = getdate()
    policy_start = get_policy_start_date(settings)

    # We need to check every month from policy_start to the previous month
    current_month_start = today.replace(day=1)
    check_date = current_month_start - timedelta(days=1)

    # Determine the range of months to check
    start_date = policy_start if policy_start else date(2000, 1, 1)

    # Loop backwards from last month to policy_start month
    while check_date >= start_date:
        month_start = check_date.replace(day=1)
        month_end = check_date # since we started at end of month

        # Evaluate this specific month
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
            {"start": month_start, "end": month_end},
            as_dict=True,
        )

        for_month = calendar.month_name[month_start.month]
        is_december = month_start.month == 12

        for row in attendance_summary:
            if not row.total_count or row.late_count:
                continue

            already_processed = frappe.db.sql("""
                SELECT name FROM `tabArcHR Policy Impact Log`
                WHERE employee = %s AND criteria = 'Reward'
                AND (
                    (to_date IS NOT NULL AND to_date BETWEEN %s AND %s)
                    OR
                    (to_date IS NULL AND created_on BETWEEN %s AND %s)
                )
            """, (row.employee, month_start, month_end, f"{month_start} 00:00:00", f"{month_end} 23:59:59"))
            if already_processed:
                continue

            apply_ontime_reward_cycle(
                row.employee,
                settings,
                from_date=month_start,
                to_date=month_end,
                for_month=for_month,
                grant_allocation=not is_december,
            )

        # Move to the previous month
        check_date = (month_start - timedelta(days=1))

def apply_ontime_reward_cycle(
    employee: str, settings=None, from_date=None, to_date=None, for_month=None, grant_allocation=True
):
    settings = settings or get_policy_impact_settings()
    max_reward_leaves = cint(settings.max_reward_leaves_per_year)

    reference_date = to_date or getdate()
    year_start = date(reference_date.year, 1, 1)
    year_end = date(reference_date.year, 12, 31)

    reward_leaves_this_year = frappe.db.sql("""
        SELECT COUNT(name) FROM `tabArcHR Policy Impact Log`
        WHERE employee = %s AND criteria = 'Reward' AND type = 'Leaves' AND status = 'Applied'
        AND (
            (to_date IS NOT NULL AND to_date BETWEEN %s AND %s)
            OR
            (to_date IS NULL AND created_on BETWEEN %s AND %s)
        )
    """, (employee, year_start, year_end, f"{year_start} 00:00:00", f"{year_end} 23:59:59"))[0][0]

    created_on = frappe.utils.now()

    if grant_allocation and reward_leaves_this_year >= max_reward_leaves:
        create_policy_impact_log(
            employee,
            criteria="Reward",
            impact_type="Salary",
            status="Pending",
            created_on=created_on,
            from_date=from_date,
            to_date=to_date,
            for_month=for_month,
        )
        return

    create_policy_impact_log(
        employee,
        criteria="Reward",
        impact_type="Leaves",
        status="Pending",
        created_on=created_on,
        from_date=from_date,
        to_date=to_date,
        for_month=for_month,
    )

def grant_reward_leave(employee: str, to_date=None, adjustment=1):
    allocation = get_active_leave_allocation(employee, "Reward Leave", date_for_allocation=to_date)
    if allocation:
        adjust_leave_allocation(allocation, adjustment)
        return

    reference_date = to_date or getdate()
    year = reference_date.year
    company = frappe.db.get_value("Employee", employee, "company")

    allocation = frappe.get_doc(
        {
            "doctype": "Leave Allocation",
            "employee": employee,
            "leave_type": "Reward Leave",
            "company": company,
            "from_date": date(year, 1, 1),
            "to_date": date(year, 12, 31),
            "new_leaves_allocated": adjustment,
            "carry_forward": 0,
        }
    )
    allocation.flags.ignore_permissions = True
    allocation.insert()
    allocation.submit()

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def get_active_leave_allocation(employee: str, leave_type: str, date_for_allocation=None):
    date_for_allocation = date_for_allocation or getdate()
    name = frappe.db.get_value(
        "Leave Allocation",
        {
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "from_date": ["<=", date_for_allocation],
            "to_date": [">=", date_for_allocation],
        },
        "name",
        order_by="to_date desc",
    )
    return frappe.get_doc("Leave Allocation", name) if name else None

def adjust_leave_allocation(allocation, delta: float):
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
