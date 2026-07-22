# Copyright (c) 2026, Shaid Azmin and contributors
# License: GNU General Public License v3. See license.txt


from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.utils import cint, getdate

Filters = frappe._dict


def execute(filters: Optional[Filters] = None) -> Tuple:
	filters = frappe._dict(filters or {})
	if filters.get("employee") == []:
		filters.pop("employee")

	date_value = filters.get("date")
	if not date_value:
		frappe.throw(_("Please select a date."))

	date = getdate(date_value)

	columns = get_columns()
	data = get_data(filters, date, date)

	return columns, data


def get_columns() -> List[Dict]:
	return [
		{"label": _("SL"), "fieldname": "sl", "fieldtype": "Int", "width": 50},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{"label": _("Employee ID"), "fieldname": "employee", "fieldtype": "Data", "width": 120},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 160},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 160,
		},
		{"label": _("Job Location"), "fieldname": "job_location", "fieldtype": "Data", "width": 130},
		{"label": _("Roster Time"), "fieldname": "roster_time", "fieldtype": "Data", "width": 170},
		{"label": _("In Time"), "fieldname": "in_time", "fieldtype": "Data", "width": 100},
		{"label": _("Minute(s) Late"), "fieldname": "minute_late", "fieldtype": "Int", "width": 110},
		{"label": _("Status"), "fieldname": "in_status", "fieldtype": "Data", "width": 90},
		{"label": _("Out Time"), "fieldname": "out_time", "fieldtype": "Data", "width": 100},
		{"label": _("Minute(s) Early"), "fieldname": "minute_early", "fieldtype": "Int", "width": 110},
		{"label": _("Status"), "fieldname": "out_status", "fieldtype": "Data", "width": 90},
	]


def get_active_or_recently_relieved_condition(Employee, filters: Filters, start_date, end_date):
	"""Employees to include when the "Is Active Employees" filter is on:
	currently Active employees, plus anyone whose Relieving Date falls
	within the selected date, so their attendance up to their last working
	day still shows instead of disappearing from the Active view entirely."""
	if not filters.get("is_active"):
		return Employee.status != "Active"

	return (Employee.status == "Active") | (
		(Employee.relieving_date >= start_date) & (Employee.relieving_date <= end_date)
	)


def get_employees(filters: Filters, start_date, end_date) -> List[Dict]:
	Employee = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(Employee)
		.select(
			Employee.name,
			Employee.employee_name,
			Employee.department,
			Employee.custom_job_location,
			Employee.default_shift,
			Employee.holiday_list,
			Employee.status,
			Employee.relieving_date,
		)
		.where(Employee.company == filters.company)
		.where(get_active_or_recently_relieved_condition(Employee, filters, start_date, end_date))
	)
	if filters.get("department"):
		query = query.where(Employee.department == filters.department)
	if filters.employee:
		employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
		query = query.where(Employee.name.isin(employees))
	query = query.orderby(Employee.employee_name)

	return query.run(as_dict=True)


def get_employee_display_name(filters: Filters, emp: Dict) -> str:
	is_inactive = emp.get("status") and emp.status != "Active"
	if filters.get("is_active") and is_inactive:
		return "{} ({})".format(emp.employee_name, _("Inactive"))
	return emp.employee_name


def get_checkins_for_date(employee_ids: List[str], date) -> Dict[str, List[Dict]]:
	if not employee_ids:
		return {}

	# Filtered on `time` directly rather than the custom `date` field -- that
	# field is populated by the checkin-creation pipeline and isn't reliably
	# set on every record, so relying on it can silently miss real checkins.
	rows = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": ["in", employee_ids],
			"time": ["between", [f"{date} 00:00:00", f"{date} 23:59:59"]],
		},
		fields=["employee", "time", "shift", "shift_start", "shift_end"],
		order_by="time asc",
	)

	checkins = {}
	for row in rows:
		checkins.setdefault(row.employee, []).append(row)
	return checkins


def get_holiday_list_for_employee(employee_holiday_list: Optional[str], company: str) -> Optional[str]:
	return employee_holiday_list or frappe.get_cached_value("Company", company, "default_holiday_list")


def get_holiday_status(holiday_list: Optional[str], date) -> Optional[str]:
	if not holiday_list:
		return None
	holiday = frappe.db.get_value(
		"Holiday", {"parent": holiday_list, "holiday_date": date}, ["weekly_off"], as_dict=True
	)
	if not holiday:
		return None
	return "Weekend" if holiday.weekly_off else "Holiday"


def format_time(value) -> str:
	if not value:
		return ""
	return value.strftime("%I:%M %p")


def get_shift_grace_periods(shift_name: Optional[str]) -> Tuple[int, int]:
	"""Returns (late_entry_grace_period, early_exit_grace_period) minutes
	configured on the Shift Type, or (0, 0) if there's no shift / none set."""
	if not shift_name:
		return 0, 0

	grace = frappe.db.get_value(
		"Shift Type", shift_name, ["late_entry_grace_period", "early_exit_grace_period"]
	)
	if not grace:
		return 0, 0

	return cint(grace[0]), cint(grace[1])


def get_roster_bounds(shift_start, shift_end, shift_name: Optional[str], date) -> Tuple[str, Optional[datetime], Optional[datetime]]:
	"""Returns (roster_time_label, roster_start, roster_end).

	shift_start/shift_end are the checkin's own resolved shift datetimes if
	available, else derived from the Shift Type's start_time/end_time for
	the given date. The Shift Type's Late Entry Grace Period is then added
	to the start (an employee isn't late until after that window) and the
	Early Exit Grace Period is subtracted from the end (an employee isn't
	early until before that window) -- the resulting window is both what's
	shown as "Roster Time" and what Minute(s) Late / Minute(s) Early are
	measured against.
	"""
	if not (shift_start and shift_end) and shift_name:
		shift_times = frappe.db.get_value("Shift Type", shift_name, ["start_time", "end_time"])
		if shift_times and shift_times[0] and shift_times[1]:
			start_time = datetime.strptime(str(shift_times[0]), "%H:%M:%S").time()
			end_time = datetime.strptime(str(shift_times[1]), "%H:%M:%S").time()
			shift_start = datetime.combine(date, start_time)
			shift_end = datetime.combine(date, end_time)

	if not (shift_start and shift_end):
		return "", None, None

	late_grace, early_grace = get_shift_grace_periods(shift_name)
	roster_start = shift_start + timedelta(minutes=late_grace)
	roster_end = shift_end - timedelta(minutes=early_grace)

	return f"{format_time(roster_start)} to {format_time(roster_end)}", roster_start, roster_end


def get_data(filters: Filters, start_date, end_date) -> List[Dict]:
	employees = get_employees(filters, start_date, end_date)
	employee_ids = [emp.name for emp in employees]
	today = getdate()

	data = []
	sl = 1
	date = start_date
	while date <= end_date:
		checkins_map = get_checkins_for_date(employee_ids, date)
		is_today = date == today

		for emp in employees:
			row = get_row_for_employee_date(filters, emp, date, is_today, checkins_map.get(emp.name, []))
			row["sl"] = sl
			sl += 1
			data.append(row)

		date += timedelta(days=1)

	return data


def get_row_for_employee_date(filters: Filters, emp: Dict, date, is_today: bool, checkins: List[Dict]) -> Dict:
	first_checkin = checkins[0] if checkins else None
	last_checkin = checkins[-1] if len(checkins) > 1 else None

	holiday_list = get_holiday_list_for_employee(emp.holiday_list, filters.company)
	holiday_status = get_holiday_status(holiday_list, date)

	shift_start = first_checkin.shift_start if first_checkin else None
	shift_end = first_checkin.shift_end if first_checkin else None
	shift_for_fallback = (first_checkin.shift if first_checkin else None) or emp.default_shift

	roster_label, roster_start, roster_end = get_roster_bounds(shift_start, shift_end, shift_for_fallback, date)
	roster_time = holiday_status if holiday_status else roster_label

	row = {
		"date": date,
		"employee": emp.name,
		"employee_name": get_employee_display_name(filters, emp),
		"department": emp.department,
		"job_location": emp.custom_job_location,
		"roster_time": roster_time,
		"in_time": "",
		"minute_late": None,
		"in_status": "",
		"out_time": "",
		"minute_early": None,
		"out_status": "",
	}

	if first_checkin:
		row["in_time"] = format_time(first_checkin.time)
		if roster_start:
			late_minutes = round(max((first_checkin.time - roster_start).total_seconds() / 60, 0))
			row["minute_late"] = late_minutes
			row["in_status"] = "LATE" if late_minutes > 0 else "INTIME"

	# Out Time / Minute(s) Early / Status only apply to a day that's already
	# finished -- for the current date the employee may still be at work,
	# so only the In Time (and its lateness) is meaningful.
	if not is_today and last_checkin:
		row["out_time"] = format_time(last_checkin.time)
		if roster_end:
			early_minutes = round(max((roster_end - last_checkin.time).total_seconds() / 60, 0))
			row["minute_early"] = early_minutes
			row["out_status"] = "Early" if early_minutes > 0 else "INTIME"

	return row
