# Copyright (c) 2026, Shaid Azmin and contributors
# License: GNU General Public License v3. See license.txt


from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.utils import getdate

Filters = frappe._dict


def execute(filters: Optional[Filters] = None) -> Tuple:
	filters = frappe._dict(filters or {})
	date_range = filters.get("date_range")
	if not date_range or len(date_range) != 2:
		frappe.throw(_("Please select a date range."))

	start_date = getdate(date_range[0])
	end_date = getdate(date_range[1])
	if start_date > end_date:
		frappe.throw(_("Start date cannot be after end date."))

	columns = get_columns()
	data = get_data(filters, start_date, end_date)

	return columns, data


def get_columns() -> List[Dict]:
	return [
		{"label": _("SL"), "fieldname": "sl", "fieldtype": "Int", "width": 50},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 100},
		{
			"label": _("Employee ID"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
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
		{"label": _("Minute Late"), "fieldname": "minute_late", "fieldtype": "Float", "width": 100},
		{"label": _("Status"), "fieldname": "in_status", "fieldtype": "Data", "width": 90},
		{"label": _("Out Time"), "fieldname": "out_time", "fieldtype": "Data", "width": 100},
		{"label": _("Minute Early"), "fieldname": "minute_early", "fieldtype": "Float", "width": 100},
		{"label": _("Status"), "fieldname": "out_status", "fieldtype": "Data", "width": 90},
	]


def get_employees(filters: Filters) -> List[Dict]:
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
		)
		.where(Employee.company == filters.company)
	)
	if filters.get("department"):
		query = query.where(Employee.department == filters.department)
	if filters.get("is_active"):
		query = query.where(Employee.status == "Active")
	else:
		query = query.where(Employee.status != "Active")
	if filters.employee:
		employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
		query = query.where(Employee.name.isin(employees))
	query = query.orderby(Employee.employee_name)

	return query.run(as_dict=True)


def get_checkins_for_date(employee_ids: List[str], date) -> Dict[str, List[Dict]]:
	if not employee_ids:
		return {}

	rows = frappe.get_all(
		"Employee Checkin",
		filters={"employee": ["in", employee_ids], "date": date},
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


def get_roster_time(shift_start, shift_end, default_shift: Optional[str], date) -> str:
	if shift_start and shift_end:
		return f"{format_time(shift_start)} to {format_time(shift_end)}"

	if not default_shift:
		return ""

	shift_times = frappe.db.get_value("Shift Type", default_shift, ["start_time", "end_time"])
	if not shift_times or not shift_times[0] or not shift_times[1]:
		return ""

	start_time = datetime.strptime(str(shift_times[0]), "%H:%M:%S").time()
	end_time = datetime.strptime(str(shift_times[1]), "%H:%M:%S").time()
	start_dt = datetime.combine(date, start_time)
	end_dt = datetime.combine(date, end_time)
	return f"{format_time(start_dt)} to {format_time(end_dt)}"


def get_data(filters: Filters, start_date, end_date) -> List[Dict]:
	employees = get_employees(filters)
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

	roster_time = (
		holiday_status if holiday_status else get_roster_time(shift_start, shift_end, shift_for_fallback, date)
	)

	row = {
		"date": date,
		"employee": emp.name,
		"employee_name": emp.employee_name,
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
		if shift_start:
			late_minutes = round(max((first_checkin.time - shift_start).total_seconds() / 60, 0), 2)
			row["minute_late"] = late_minutes
			row["in_status"] = "LATE" if late_minutes > 0 else "INTIME"

	# Out Time / Minute Early / Status only apply to a day that's already
	# finished -- for the current date the employee may still be at work,
	# so only the In Time (and its lateness) is meaningful.
	if not is_today and last_checkin:
		row["out_time"] = format_time(last_checkin.time)
		if last_checkin.shift_end:
			early_minutes = round(
				max((last_checkin.shift_end - last_checkin.time).total_seconds() / 60, 0), 2
			)
			row["minute_early"] = early_minutes
			row["out_status"] = "Early" if early_minutes > 0 else "INTIME"

	return row
