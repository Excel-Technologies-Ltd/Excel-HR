# Copyright (c) 2026, Shaid Azmin and contributors
# License: GNU General Public License v3. See license.txt


from datetime import timedelta
from typing import Dict, List, Optional, Set, Tuple

import frappe
from frappe import _
from frappe.utils import getdate

Filters = frappe._dict

# Order matters: it drives both the tally dict and the Total sum.
COUNT_FIELDS = [
	"present",
	"leave",
	"weekly_off",
	"holiday",
	"wfh",
	"leave_application",
	"ar_application",
	"absent",
]


def execute(filters: Optional[Filters] = None) -> Tuple:
	filters = frappe._dict(filters or {})
	if filters.get("employee") == []:
		filters.pop("employee")

	date_range = filters.get("date_range")
	if not date_range or not date_range[0] or not date_range[1]:
		frappe.throw(_("Please select a Date Range."))

	filters.date_range = [getdate(date_range[0]), getdate(date_range[1])]

	columns = get_columns()
	data = get_data(filters)

	if not data:
		frappe.msgprint(_("No employees found for this criteria."), alert=True, indicator="orange")
		return columns, [], get_message(), None

	return columns, data, get_message(), None


def get_message() -> str:
	legend = [
		("P", _("Present"), "green"),
		("L", _("Leave"), "#318AD8"),
		("WO", _("Weekly Off"), "brown"),
		("H", _("Holiday"), "brown"),
		("WFH", _("Work From Home"), "green"),
		("L.App", _("Leave Application"), "#318AD8"),
		("AR.App", _("Attendance Req. Application"), "orange"),
		("A", _("Absent"), "red"),
	]

	message = "<div style='display:flex;flex-wrap:wrap;'>"
	for abbr, label, color in legend:
		message += f"""
			<span style='font-size:10px; color:{color}; padding-right: 12px; padding-left: 5px; margin-right: 3px; display: inline-block;'>
				&#8718; {abbr} = {label}
			</span>
		"""
	message += "</div>"
	return message


def get_columns() -> List[Dict]:
	return [
		
		{"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 130,
		},
		{"label": _("Company"), "fieldname": "company", "fieldtype": "Link", "options": "Company", "width": 130},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 130,
		},
		{"label": _("Section"), "fieldname": "section", "fieldtype": "Link", "options": "Department", "width": 130},
		{
			"label": _("Sub-section"),
			"fieldname": "sub_section",
			"fieldtype": "Link",
			"options": "Department",
			"width": 130,
		},
		{"label": _("P"), "fieldname": "present", "fieldtype": "Float", "width": 70},
		{"label": _("P%"), "fieldname": "present_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("L"), "fieldname": "leave", "fieldtype": "Float", "width": 70},
		{"label": _("L%"), "fieldname": "leave_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("WO"), "fieldname": "weekly_off", "fieldtype": "Float", "width": 70},
		{"label": _("WO%"), "fieldname": "weekly_off_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("H"), "fieldname": "holiday", "fieldtype": "Float", "width": 70},
		{"label": _("H%"), "fieldname": "holiday_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("WFH"), "fieldname": "wfh", "fieldtype": "Float", "width": 70},
		{"label": _("WFH%"), "fieldname": "wfh_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("L.App"), "fieldname": "leave_application", "fieldtype": "Float", "width": 80},
		{"label": _("L.App%"), "fieldname": "leave_application_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("AR.App"), "fieldname": "ar_application", "fieldtype": "Float", "width": 80},
		{"label": _("AR.App%"), "fieldname": "ar_application_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("A"), "fieldname": "absent", "fieldtype": "Float", "width": 70},
		{"label": _("A%"), "fieldname": "absent_percent", "fieldtype": "Percent", "width": 90},
		{"label": _("Total"), "fieldname": "total", "fieldtype": "Float", "width": 90},
	]


def get_employees(filters: Filters) -> List[Dict]:
	"""Returns Employees matching the report filters whose employment period
	overlaps the selected date range at all (joined on/before the range ends,
	and either still active or relieved on/after the range starts)."""
	from_date, to_date = filters.date_range

	Employee = frappe.qb.DocType("Employee")
	query = frappe.qb.from_(Employee).select(
		Employee.name,
		Employee.employee_name,
		Employee.designation,
		Employee.company,
		Employee.excel_parent_department.as_("department"),
		Employee.excel_hr_section.as_("section"),
		Employee.excel_hr_sub_section.as_("sub_section"),
		Employee.holiday_list,
		Employee.date_of_joining,
		Employee.relieving_date,
	)

	if filters.company:
		query = query.where(Employee.company == filters.company)
	if filters.custom_job_location:
		query = query.where(Employee.custom_job_location == filters.custom_job_location)
	if filters.excel_department:
		query = query.where(Employee.excel_parent_department == filters.excel_department)
	if filters.excel_section:
		query = query.where(Employee.excel_hr_section == filters.excel_section)
	if filters.excel_sub_section:
		query = query.where(Employee.excel_hr_sub_section == filters.excel_sub_section)
	if filters.employee:
		employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
		query = query.where(Employee.name.isin(employees))

	query = query.where(
		(Employee.date_of_joining.isnull() | (Employee.date_of_joining <= to_date))
		& (Employee.relieving_date.isnull() | (Employee.relieving_date >= from_date))
	)
	query = query.orderby(Employee.employee_name)

	return query.run(as_dict=True)


def get_attendance_map(employee_ids: List[str], from_date, to_date) -> Dict[str, Dict]:
	"""Returns {employee: {date: status}} from submitted Attendance records in
	the date range -- one status per employee per day."""
	if not employee_ids:
		return {}

	Attendance = frappe.qb.DocType("Attendance")
	rows = (
		frappe.qb.from_(Attendance)
		.select(Attendance.employee, Attendance.attendance_date, Attendance.status)
		.where(
			(Attendance.docstatus == 1)
			& Attendance.employee.isin(employee_ids)
			& (Attendance.attendance_date >= from_date)
			& (Attendance.attendance_date <= to_date)
		)
	).run(as_dict=True)

	attendance_map: Dict[str, Dict] = {}
	for r in rows:
		attendance_map.setdefault(r.employee, {})[getdate(r.attendance_date)] = r.status
	return attendance_map


def get_holiday_map(holiday_lists: List[str], from_date, to_date) -> Dict[str, Dict]:
	"""Returns {holiday_list: {date: is_weekly_off}} for every Holiday List
	entry falling within the date range."""
	holiday_lists = [h for h in holiday_lists if h]
	if not holiday_lists:
		return {}

	Holiday = frappe.qb.DocType("Holiday")
	rows = (
		frappe.qb.from_(Holiday)
		.select(Holiday.parent, Holiday.holiday_date, Holiday.weekly_off)
		.where(
			Holiday.parent.isin(holiday_lists)
			& (Holiday.holiday_date >= from_date)
			& (Holiday.holiday_date <= to_date)
		)
	).run(as_dict=True)

	holiday_map: Dict[str, Dict] = {}
	for r in rows:
		holiday_map.setdefault(r.parent, {})[getdate(r.holiday_date)] = bool(r.weekly_off)
	return holiday_map


def get_date_span_map(rows: List[Dict], from_date, to_date) -> Dict[str, Set]:
	"""Common helper: turns a list of {employee, from_date, to_date} rows into
	{employee: {dates}}, clipped to the report's date range."""
	days_map: Dict[str, Set] = {}
	for r in rows:
		start = max(getdate(r.from_date), from_date)
		end = min(getdate(r.to_date), to_date)
		d = start
		while d <= end:
			days_map.setdefault(r.employee, set()).add(d)
			d += timedelta(days=1)
	return days_map


def get_leave_application_days(employee_ids: List[str], from_date, to_date) -> Dict[str, Set]:
	"""Returns {employee: {dates}} for open (pending) Leave Applications
	overlapping the date range -- these show as "L.App" since they haven't
	been approved into an actual Attendance record yet."""
	if not employee_ids:
		return {}

	LeaveApplication = frappe.qb.DocType("Leave Application")
	rows = (
		frappe.qb.from_(LeaveApplication)
		.select(LeaveApplication.employee, LeaveApplication.from_date, LeaveApplication.to_date)
		.where(
			(LeaveApplication.docstatus == 0)
			& (LeaveApplication.status == "Open")
			& LeaveApplication.employee.isin(employee_ids)
			& (LeaveApplication.from_date <= to_date)
			& (LeaveApplication.to_date >= from_date)
		)
	).run(as_dict=True)

	return get_date_span_map(rows, from_date, to_date)


def get_attendance_request_days(employee_ids: List[str], from_date, to_date) -> Dict[str, Set]:
	"""Returns {employee: {dates}} for pending (Applied, not yet submitted)
	Attendance Requests overlapping the date range -- these show as
	"AR.App" since they haven't been submitted into an actual Attendance
	record yet."""
	if not employee_ids:
		return {}

	AttendanceRequest = frappe.qb.DocType("Attendance Request")
	rows = (
		frappe.qb.from_(AttendanceRequest)
		.select(AttendanceRequest.employee, AttendanceRequest.from_date, AttendanceRequest.to_date)
		.where(
			(AttendanceRequest.docstatus == 0)
			& (AttendanceRequest.workflow_state == "Applied")
			& AttendanceRequest.employee.isin(employee_ids)
			& (AttendanceRequest.from_date <= to_date)
			& (AttendanceRequest.to_date >= from_date)
		)
	).run(as_dict=True)

	return get_date_span_map(rows, from_date, to_date)


def get_data(filters: Filters) -> List[Dict]:
	from_date, to_date = filters.date_range
	total_days = (to_date - from_date).days + 1

	employees = get_employees(filters)
	if not employees:
		return []

	employee_ids = [emp.name for emp in employees]
	default_holiday_list = (
		frappe.get_cached_value("Company", filters.company, "default_holiday_list") if filters.company else None
	)

	attendance_map = get_attendance_map(employee_ids, from_date, to_date)
	holiday_lists = list({emp.holiday_list for emp in employees} | {default_holiday_list})
	holiday_map = get_holiday_map(holiday_lists, from_date, to_date)
	leave_application_days = get_leave_application_days(employee_ids, from_date, to_date)
	attendance_request_days = get_attendance_request_days(employee_ids, from_date, to_date)

	data = []
	for emp in employees:
		holidays = holiday_map.get(emp.holiday_list or default_holiday_list, {})
		emp_attendance = attendance_map.get(emp.name, {})
		emp_leave_app_days = leave_application_days.get(emp.name, set())
		emp_ar_app_days = attendance_request_days.get(emp.name, set())

		counts = dict.fromkeys(COUNT_FIELDS, 0.0)

		current_date = from_date
		while current_date <= to_date:
			status = emp_attendance.get(current_date)

			if status == "Present":
				counts["present"] += 1
			elif status == "Absent":
				counts["absent"] += 1
			elif status == "Half Day":
				# Split evenly: half the day worked, half taken as leave.
				counts["present"] += 0.5
				counts["leave"] += 0.5
			elif status == "Work From Home":
				counts["wfh"] += 1
			elif status == "On Leave":
				counts["leave"] += 1
			elif current_date in holidays:
				if holidays[current_date]:
					counts["weekly_off"] += 1
				else:
					counts["holiday"] += 1
			elif current_date in emp_leave_app_days:
				counts["leave_application"] += 1
			elif current_date in emp_ar_app_days:
				counts["ar_application"] += 1
			else:
				counts["absent"] += 1

			current_date += timedelta(days=1)

		row = {
			"employee": emp.name,
			"employee_name": emp.employee_name,
			"designation": emp.designation,
			"company": emp.company,
			"department": emp.department,
			"section": emp.section,
			"sub_section": emp.sub_section,
		}
		row.update(counts)
		row["total"] = sum(counts[field] for field in COUNT_FIELDS)

		for field in COUNT_FIELDS:
			row[f"{field}_percent"] = round((counts[field] / total_days) * 100, 2) if total_days else 0.0

		data.append(row)

	return data
