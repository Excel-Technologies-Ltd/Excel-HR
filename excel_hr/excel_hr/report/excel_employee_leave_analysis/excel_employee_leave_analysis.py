# Copyright (c) 2026, Shaid Azmin and contributors
# License: GNU General Public License v3. See license.txt


from calendar import monthrange
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.query_builder.functions import Extract, Sum
from frappe.utils import cint, cstr, getdate

Filters = frappe._dict

# Mnemonic codes for each Leave Type, e.g. "Annual Leave" -> "AL". Any Leave
# Type not listed here (a newly added one) falls back to get_leave_abbr()'s
# initials-based guess so the report never has to be touched again just
# because HR added a new leave type.
LEAVE_TYPE_ABBR = {
	"Annual Leave": "AL",
	"Compensatory Leave": "CL",
	"Leave Without Pay": "LWP",
	"Maternity Leave": "MTL",
	"Monthly Paid Leave": "MPL",
	"Special Leave": "SPL",
	"Reward Leave": "RL",
}

day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def get_leave_abbr(leave_type: str) -> str:
	if not leave_type:
		return ""
	if leave_type in LEAVE_TYPE_ABBR:
		return LEAVE_TYPE_ABBR[leave_type]
	return "".join(word[0].upper() for word in leave_type.split() if word)


def execute(filters: Optional[Filters] = None) -> Tuple:
	filters = frappe._dict(filters or {})
	if filters.get("employee") == []:
		filters.pop("employee")

	if not (filters.month and filters.year):
		frappe.throw(_("Please select month and year."))

	leave_map = get_leave_map(filters)

	columns = get_columns(filters)
	data = get_data(filters, leave_map)

	if not data:
		frappe.msgprint(
			_("No leave records found for this criteria."), alert=True, indicator="orange"
		)
		return columns, [], None

	message = get_message() if filters.show_abbr else ""

	return columns, data, message


def get_message() -> str:
	message = ""
	colors = ["#318AD8", "green", "orange", "purple", "brown", "#318AD8"]

	count = 0
	for leave_type in get_all_leave_types():
		abbr = get_leave_abbr(leave_type)
		color = colors[count % len(colors)]
		message += f"""
			<span style='border-left: 2px solid {color}; padding-right: 12px; padding-left: 5px; margin-right: 3px;'>
				{leave_type} - {abbr}
			</span>
		"""
		count += 1

	return message


def get_all_leave_types() -> List[str]:
	return frappe.db.sql_list("select name from `tabLeave Type` order by name asc")


def get_columns(filters: Filters) -> List[Dict]:
	columns = [
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 135,
		},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
	]

	if filters.summarized_view:
		for leave_type in get_all_leave_types():
			columns.append(
				{
					"label": _(f"{leave_type} ({get_leave_abbr(leave_type)})"),
					"fieldname": frappe.scrub(leave_type),
					"fieldtype": "Float",
					"width": 130,
				}
			)
		columns.append(
			{"label": _("Total Leave Days"), "fieldname": "total_leave_days", "fieldtype": "Float", "width": 130}
		)
	else:
		columns.extend(get_columns_for_days(filters))

	return columns


def get_columns_for_days(filters: Filters) -> List[Dict]:
	total_days = get_total_days_in_month(filters)
	days = []

	for day in range(1, total_days + 1):
		day_s = cstr(day)
		date_str = "{}-{}-{}".format(cstr(filters.year), cstr(filters.month), day_s)
		weekday = day_abbr[getdate(date_str).weekday()]
		label = "{} {}".format(day_s, weekday)
		days.append({"label": label, "fieldtype": "Data", "fieldname": day_s, "width": 65})

	return days


def get_total_days_in_month(filters: Filters) -> int:
	return monthrange(cint(filters.year), cint(filters.month))[1]


def get_relieved_in_range_dates(filters: Filters) -> Tuple[str, str]:
	total_days = get_total_days_in_month(filters)
	month_start = "{}-{:02d}-01".format(cint(filters.year), cint(filters.month))
	month_end = "{}-{:02d}-{:02d}".format(cint(filters.year), cint(filters.month), total_days)
	return month_start, month_end


def get_active_or_recently_relieved_condition(Employee, filters: Filters):
	"""Employees to include when the "Is Active Employees" filter is on:
	currently Active employees, plus anyone relieved during the selected
	month, so their leave data up to their last working day still shows
	instead of disappearing from the Active view entirely."""
	if not filters.get("is_active"):
		return Employee.status != "Active"

	month_start, month_end = get_relieved_in_range_dates(filters)
	return (Employee.status == "Active") | (
		(Employee.relieving_date >= month_start) & (Employee.relieving_date <= month_end)
	)


def get_employee_related_details(filters: Filters) -> Dict:
	Employee = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(Employee)
		.select(
			Employee.name,
			Employee.employee_name,
			Employee.department,
			Employee.default_shift,
			Employee.status,
			Employee.relieving_date,
		)
		.where(Employee.company == filters.company)
		.where(get_active_or_recently_relieved_condition(Employee, filters))
	)
	if filters.get("department"):
		query = query.where(Employee.department == filters.department)
	if filters.employee:
		employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
		query = query.where(Employee.name.isin(employees))

	emp_map = {}
	for emp in query.run(as_dict=True):
		emp_map[emp.name] = emp

	return emp_map


def get_leave_map(filters: Filters) -> Dict:
	"""Returns {employee: {day_of_month: leave_type}} built from both
	submitted (On Leave) Attendance records and pending Leave Application
	drafts, so the report shows leave data as soon as it's requested, not just
	once payroll has processed it."""
	leave_map = {}

	Attendance = frappe.qb.DocType("Attendance")
	Employee = frappe.qb.DocType("Employee")

	employee_subquery = (
		frappe.qb.from_(Employee).select(Employee.name).where(Employee.company == filters.company)
	)
	if filters.department:
		employee_subquery = employee_subquery.where(Employee.department == filters.department)
	employee_subquery = employee_subquery.where(get_active_or_recently_relieved_condition(Employee, filters))

	query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.employee,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.leave_type,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.status == "On Leave")
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
			& Attendance.employee.isin(employee_subquery)
		)
	)
	if filters.employee:
		employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
		query = query.where(Attendance.employee.isin(employees))

	for d in query.run(as_dict=True):
		leave_map.setdefault(d.employee, {})[d.day_of_month] = d.leave_type

	for lr in get_draft_leave_applications(filters):
		if lr.start_date is None or lr.to_date is None:
			continue

		if lr.start_month == lr.to_month:
			day_range = range(lr.start_date, lr.to_date + 1)
		elif int(filters.month) == int(lr.start_month):
			day_range = range(lr.start_date, get_total_days_in_month(filters) + 1)
		elif int(filters.month) == int(lr.to_month):
			day_range = range(1, lr.to_date + 1)
		else:
			continue

		for day in day_range:
			leave_map.setdefault(lr.employee, {}).setdefault(day, lr.leave_type)

	return leave_map


def get_draft_leave_applications(filters: Filters) -> List[Dict]:
	LeaveApp = frappe.qb.DocType("Leave Application")
	Employee = frappe.qb.DocType("Employee")
	status_condition = get_active_or_recently_relieved_condition(Employee, filters)

	query = (
		frappe.qb.from_(LeaveApp)
		.join(Employee)
		.on(Employee.name == LeaveApp.employee)
		.select(
			LeaveApp.employee,
			LeaveApp.leave_type,
			Extract("day", LeaveApp.from_date).as_("start_date"),
			Extract("day", LeaveApp.to_date).as_("to_date"),
			Extract("month", LeaveApp.from_date).as_("start_month"),
			Extract("month", LeaveApp.to_date).as_("to_month"),
		)
		.where(
			(LeaveApp.docstatus == 0)
			& (LeaveApp.status == "Open")
			& (Employee.company == filters.company)
			& (
				(Extract("month", LeaveApp.from_date) == filters.month)
				| (Extract("month", LeaveApp.to_date) == filters.month)
			)
			& (
				(Extract("year", LeaveApp.from_date) == filters.year)
				| (Extract("year", LeaveApp.to_date) == filters.year)
			)
			& status_condition
		)
	)
	if filters.department:
		query = query.where(Employee.department == filters.department)
	if filters.employee:
		employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
		query = query.where(LeaveApp.employee.isin(employees))

	return query.run(as_dict=True)


def get_employee_display_name(filters: Filters, details) -> str:
	is_inactive = details.get("status") and details.status != "Active"
	if filters.get("is_active") and is_inactive:
		return "{} ({})".format(details.employee_name, _("Inactive"))
	return details.employee_name


def get_data(filters: Filters, leave_map: Dict) -> List[Dict]:
	employee_details = get_employee_related_details(filters)
	data = []

	if filters.summarized_view:
		leave_types = get_all_leave_types()
		for employee, details in employee_details.items():
			row = {"employee": employee, "employee_name": get_employee_display_name(filters, details)}
			summary = get_leave_summary(employee, filters)
			total = 0.0
			for leave_type in leave_types:
				days = summary.get(frappe.scrub(leave_type), 0)
				row[frappe.scrub(leave_type)] = days
				total += days
			row["total_leave_days"] = total
			data.append(row)
	else:
		for employee, details in employee_details.items():
			row = get_leave_status_for_detailed_view(filters, leave_map.get(employee))
			row.update({"employee": employee, "employee_name": get_employee_display_name(filters, details)})
			data.append(row)

	return data


def get_leave_status_for_detailed_view(filters: Filters, day_map: Optional[Dict]) -> Dict:
	"""Returns a single date-wise row for the employee with the Leave Type
	abbreviation on leave days and a blank cell on every other day (present,
	absent, holiday, weekend -- all of it)."""
	total_days = get_total_days_in_month(filters)
	day_map = day_map or {}

	row = {}
	for day in range(1, total_days + 1):
		leave_type = day_map.get(day)
		row[cstr(day)] = get_leave_abbr(leave_type) if leave_type else ""

	return row


def get_leave_summary(employee: str, filters: Filters) -> Dict[str, float]:
	Attendance = frappe.qb.DocType("Attendance")
	day_case = frappe.qb.terms.Case().when(Attendance.status == "Half Day", 0.5).else_(1)
	sum_leave_days = Sum(day_case).as_("leave_days")

	leave_details = (
		frappe.qb.from_(Attendance)
		.select(Attendance.leave_type, sum_leave_days)
		.where(
			(Attendance.employee == employee)
			& (Attendance.docstatus == 1)
			& (Attendance.status == "On Leave")
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
		.groupby(Attendance.leave_type)
	).run(as_dict=True)

	return {frappe.scrub(d.leave_type): d.leave_days for d in leave_details if d.leave_type}
