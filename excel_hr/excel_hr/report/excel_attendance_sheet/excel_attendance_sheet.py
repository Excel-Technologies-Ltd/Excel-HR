# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from calendar import monthrange
from datetime import date, datetime
from itertools import groupby
from typing import Dict, List, Optional, Tuple

import frappe
from frappe import _
from frappe.query_builder.functions import Count, Extract, Sum
from frappe.utils import cint, cstr, getdate
from excel_hr.excel_hr.report.attendance_checkin_utils import get_local_checkin_tags, local_tag
Filters = frappe._dict


status_map = {
	"Present": "P",
	"Absent": "A",
	"Half Day": "HD",
	"Work From Home": "WFH",
	"On Leave": "L",
	"Holiday": "H/WO",
	"Weekly Off": "H/WO",
 	"Attendance Request": "A.App",
    "Leave Application": "L.App",
}

day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def execute(filters: Optional[Filters] = None) -> Tuple:
	filters = frappe._dict(filters or {})
	if filters.get("employee") == []:
		filters.pop("employee")

	if not (filters.month and filters.year):
		frappe.throw(_("Please select month and year."))

	attendance_map, holiday_anchors = get_attendance_map(filters)
	present_day_tags = get_present_day_tags(filters)

	# Modified: Removed the check that prevents empty data from showing
	# if not attendance_map:
	# 	return [], [], None, None

	columns = get_columns(filters)
	data = get_data(filters, attendance_map, holiday_anchors, present_day_tags)

	if not data:
		frappe.msgprint(
			_("No attendance records found for this criteria."), alert=True, indicator="orange"
		)
		return columns, [], None, None

	message = get_message() if not filters.summarized_view else ""
	chart = get_chart_data(attendance_map, filters)

	return columns, data, message, chart


def get_message() -> str:
	message = ""
	colors = ["green", "red", "orange", "green", "#318AD8", "purple", "brown", "orange", "orange"]

	count = 0
	seen_abbrs = set()
	for status, abbr in status_map.items():
		if abbr in seen_abbrs:
			continue
		seen_abbrs.add(abbr)

		color = colors[count % len(colors)]
		message += f"""
			<span style='border-left: 2px solid {color}; padding-right: 12px; padding-left: 5px; margin-right: 3px;'>
				{status} - {abbr}
			</span>
		"""
		count += 1

	return message


def get_columns(filters: Filters) -> List[Dict]:
	columns = []

	if filters.group_by:
		options_mapping = {
			"Branch": "Branch",
			"Grade": "Employee Grade",
			"Department": "Department",
			"Designation": "Designation",
		}
		options = options_mapping.get(filters.group_by)
		columns.append(
			{
				"label": _(filters.group_by),
				"fieldname": frappe.scrub(filters.group_by),
				"fieldtype": "Link",
				"options": options,
				"width": 120,
			}
		)

	columns.extend(
		[
			{
				"label": _("Employee"),
				"fieldname": "employee",
				"fieldtype": "Link",
				"options": "Employee",
				"width": 135,
			},
			{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 120},

		]
	)

	if filters.summarized_view:
		columns.extend(
			[
				{
					"label": _("Total Present"),
					"fieldname": "total_present",
					"fieldtype": "Float",
					"width": 110,
				},
				{"label": _("Total Leaves"), "fieldname": "total_leaves", "fieldtype": "Float", "width": 110},
				{"label": _("Total Absent"), "fieldname": "total_absent", "fieldtype": "Float", "width": 110},
				{
					"label": _("Total Holidays"),
					"fieldname": "total_holidays",
					"fieldtype": "Float",
					"width": 120,
				},
				{
					"label": _("Unmarked Days"),
					"fieldname": "unmarked_days",
					"fieldtype": "Float",
					"width": 130,
				},
			]
		)
		columns.extend(get_columns_for_leave_types())
		columns.extend(
			[
				{
					"label": _("Total Late Entries"),
					"fieldname": "total_late_entries",
					"fieldtype": "Float",
					"width": 140,
				},
				{
					"label": _("Total Early Exits"),
					"fieldname": "total_early_exits",
					"fieldtype": "Float",
					"width": 140,
				},
			]
		)
	else:
		columns.append(
			{"label": _("Current Shift"), "fieldname": "current_shift", "fieldtype": "Data", "width": 150}
		)
		columns.extend(get_columns_for_days(filters))

	return columns


def get_columns_for_leave_types() -> List[Dict]:
	leave_types = frappe.db.get_all("Leave Type", pluck="name")
	types = []
	for entry in leave_types:
		types.append(
			{"label": entry, "fieldname": frappe.scrub(entry), "fieldtype": "Float", "width": 120}
		)

	return types


def get_columns_for_days(filters: Filters) -> List[Dict]:
	total_days = get_total_days_in_month(filters)
	days = []

	for day in range(1, total_days + 1):
		day = cstr(day)
		# forms the dates from selected year and month from filters
		date = "{}-{}-{}".format(cstr(filters.year), cstr(filters.month), day)
		# gets abbr from weekday number
		weekday = day_abbr[getdate(date).weekday()]
		# sets days as 1 Mon, 2 Tue, 3 Wed
		label = "{} {}".format(day, weekday)
		days.append({"label": label, "fieldtype": "Data", "fieldname": day, "width": 65})

	return days


def get_total_days_in_month(filters: Filters) -> int:
	return monthrange(cint(filters.year), cint(filters.month))[1]

# MODIFIED: Added include_all=True parameter to get_rows call to include all employees
def get_data(filters: Filters, attendance_map: Dict, holiday_anchors: Dict, present_day_tags: Dict) -> List[Dict]:
	employee_details, group_by_param_values = get_employee_related_details(filters)
	holiday_map = get_holiday_map(filters)
	data = []

	if filters.group_by:
		group_by_column = frappe.scrub(filters.group_by)

		for value in group_by_param_values:
			if not value:
				continue

			# Modified: Added include_all=True parameter to get_rows call
			records = get_rows(
				employee_details[value], filters, holiday_map, attendance_map, holiday_anchors,
				present_day_tags, include_all=True,
			)

			if records:
				data.append({group_by_column: value})
				data.extend(records)
	else:
		# Modified: Added include_all=True parameter to get_rows call
		data = get_rows(
			employee_details, filters, holiday_map, attendance_map, holiday_anchors, present_day_tags,
			include_all=True,
		)

	return data


def get_active_or_recently_relieved_condition(Employee, filters: Filters):
	"""Employees to include when the "Is Active Employees" filter is on:
	currently Active employees, plus anyone relieved during the selected
	month, so their attendance up to their last working day still shows
	instead of disappearing from the Active view entirely."""
	if not filters.get("is_active"):
		return Employee.status != "Active"

	total_days = get_total_days_in_month(filters)
	month_start = "{}-{:02d}-01".format(cint(filters.year), cint(filters.month))
	month_end = "{}-{:02d}-{:02d}".format(cint(filters.year), cint(filters.month), total_days)

	return (Employee.status == "Active") | (
		(Employee.relieving_date >= month_start) & (Employee.relieving_date <= month_end)
	)


def get_present_day_tags(filters: Filters) -> Dict[str, Dict[int, str]]:
	"""For each employee/day marked Present, work out the extra tag to append
	to the "P" abbreviation: "AR" if the Attendance's own attendance_request
	field is set (takes priority, since it means HR filed a request to explain
	that day), else "RC" (Remote Checkin) if the employee's IN and/or OUT
	checkin that day was made on the set_local device. Returns
	{employee: {day_of_month: tag}}.
	"""
	Attendance = frappe.qb.DocType("Attendance")
	Employee = frappe.qb.DocType("Employee")

	employee_subquery = (
		frappe.qb.from_(Employee)
		.select(Employee.name)
		.where(Employee.company == filters.company)
	)
	if filters.department:
		employee_subquery = employee_subquery.where(Employee.department == filters.department)
	employee_subquery = employee_subquery.where(get_active_or_recently_relieved_condition(Employee, filters))

	query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.employee,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.attendance_date,
			Attendance.attendance_request,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.status == "Present")
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
			& Attendance.employee.isin(employee_subquery)
		)
	)
	if filters.employee:
		employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
		query = query.where(Attendance.employee.isin(employees))

	rows = query.run(as_dict=True)
	if not rows:
		return {}

	total_days = get_total_days_in_month(filters)
	checkin_tags = get_local_checkin_tags(
		list({row.employee for row in rows}),
		date(cint(filters.year), cint(filters.month), 1),
		date(cint(filters.year), cint(filters.month), total_days),
	)

	tags = {}
	for row in rows:
		if row.attendance_request:
			tag = "AR"
		else:
			attendance_date = getdate(row.attendance_date)
			is_local_checkin = local_tag(checkin_tags, row.employee, attendance_date, "IN") or local_tag(
				checkin_tags, row.employee, attendance_date, "OUT"
			)
			tag = "RC" if is_local_checkin else None
		if tag:
			tags.setdefault(row.employee, {})[row.day_of_month] = tag

	return tags

def get_attendance_map(filters: Filters) -> Tuple[Dict, Dict]:
    """Returns
    1. a dictionary of employee-wise, date-wise attendance status for the month
       (one status per employee per day, regardless of how many shifts/records
       exist for that day)
    2. a dictionary of employee-wise list of (day_of_month, holiday_list) drawn
       from their actual Attendance records, sorted ascending by day -- used to
       resolve which Holiday List was in effect around a gap in attendance.
    """
    attendance_list = get_attendance_records(filters)
    attendance_map = {}
    leave_map = {}
    holiday_anchors = {}

    # Process attendance records
    for d in attendance_list:
        if d.holiday_list:
            holiday_anchors.setdefault(d.employee, []).append((d.day_of_month, d.holiday_list))

        if d.status == "On Leave":
            leave_map.setdefault(d.employee, []).append(d.day_of_month)
            continue

        attendance_map.setdefault(d.employee, {})[d.day_of_month] = d.status

    # leave is applicable for the entire day
    for employee, leave_days in leave_map.items():
        attendance_map.setdefault(employee, {})
        for day in leave_days:
            attendance_map[employee][day] = "On Leave"

    # Process draft data for leave and attendance requests
    draft_data = get_draft_requests(filters)

    for lr in draft_data.get("leave_applications", []):
        if lr.start_date is None or lr.to_date is None:
            continue
        if lr.start_month == lr.to_month:
            for day in range(lr.start_date, lr.to_date + 1):
                attendance_map.setdefault(lr.employee, {})[day] = "Leave Application"
        else:
            if int(filters.month) == int(lr.start_month):
                for day in range(lr.start_date, get_total_days_in_month(filters) + 1):
                    attendance_map.setdefault(lr.employee, {})[day] = "Leave Application"
            elif int(filters.month) == int(lr.to_month):
                for day in range(1, lr.to_date + 1):
                    attendance_map.setdefault(lr.employee, {})[day] = "Leave Application"

    # Process attendance requests
    for ar in draft_data.get("attendance_requests", []):
        if ar.start_date is None or ar.to_date is None:
            continue
        if ar.start_month == ar.to_month:
            for day in range(ar.start_date, ar.to_date + 1):
                attendance_map.setdefault(ar.employee, {})[day] = "Attendance Request"
        else:
            if int(filters.month) == int(ar.start_month):
                for day in range(ar.start_date, get_total_days_in_month(filters) + 1):
                    attendance_map.setdefault(ar.employee, {})[day] = "Attendance Request"
            elif int(filters.month) == int(ar.to_month):
                for day in range(1, ar.to_date + 1):
                    attendance_map.setdefault(ar.employee, {})[day] = "Attendance Request"

    for employee in holiday_anchors:
        holiday_anchors[employee].sort(key=lambda entry: entry[0])

    return attendance_map, holiday_anchors


def get_draft_requests(filters: Filters) -> Dict:
    """Returns draft leave applications and attendance requests"""
    LeaveApp = frappe.qb.DocType("Leave Application")
    Employee = frappe.qb.DocType("Employee")
    AttendanceRequest = frappe.qb.DocType("Attendance Request")
    
    # Status condition
    status_condition = get_active_or_recently_relieved_condition(Employee, filters)

    # Department condition
    department_condition = None
    if filters.get("department"):
        department_condition = (Employee.department == filters.department)
    
    # Query draft leave applications
    leave_query = (
        frappe.qb.from_(LeaveApp)
        .join(Employee).on(Employee.name == LeaveApp.employee)
        .select(
            LeaveApp.employee,
            Extract("day", LeaveApp.from_date).as_("start_date"),
            Extract("day", LeaveApp.to_date).as_("to_date"),
            Extract("month", LeaveApp.from_date).as_("start_month"),
            Extract("month", LeaveApp.to_date).as_("to_month"),
        )
        .where(
            (LeaveApp.docstatus == 0)
            & (LeaveApp.status == "Open")
            & (
                (Extract("month", LeaveApp.from_date) == filters.month) |
                (Extract("month", LeaveApp.to_date) == filters.month)
            )
            & (
                (Extract("year", LeaveApp.from_date) == filters.year) |
                (Extract("year", LeaveApp.to_date) == filters.year)
            )
            & (status_condition)
        )
    )
    
    if department_condition:
        leave_query = leave_query.where(department_condition)
    
    leave_apps = leave_query.run(as_dict=True)
    
    # Query draft attendance requests
    att_query = (
        frappe.qb.from_(AttendanceRequest)
        .join(Employee).on(Employee.name == AttendanceRequest.employee)
        .select(
            AttendanceRequest.employee,
            Extract("day", AttendanceRequest.from_date).as_("start_date"),
            Extract("day", AttendanceRequest.to_date).as_("to_date"),
            Extract("month", AttendanceRequest.from_date).as_("start_month"),
            Extract("month", AttendanceRequest.to_date).as_("to_month"),
        )
        .where(
            (AttendanceRequest.docstatus == 0)
            & (AttendanceRequest.workflow_state == "Applied")
            & (AttendanceRequest.company == filters.company)
            & (
                (Extract("month", AttendanceRequest.from_date) == filters.month) |
                (Extract("month", AttendanceRequest.to_date) == filters.month)
            )
            & (
                (Extract("year", AttendanceRequest.from_date) == filters.year) |
                (Extract("year", AttendanceRequest.to_date) == filters.year)
            )
            & (status_condition)
        )
    )
    
    if department_condition:
        att_query = att_query.where(department_condition)
    
    att_requests = att_query.run(as_dict=True)
    
    return {
        "leave_applications": leave_apps,
        "attendance_requests": att_requests,
    }


def get_attendance_records(filters: Filters) -> List[Dict]:
	Attendance = frappe.qb.DocType("Attendance")
	Employee = frappe.qb.DocType("Employee")
	employee_subquery = (
        frappe.qb.from_(Employee)
        .select(Employee.name)
        .where(Employee.company == filters.company)
    )
	if filters.department:
		employee_subquery = employee_subquery.where(Employee.department == filters.department)
	employee_subquery = employee_subquery.where(get_active_or_recently_relieved_condition(Employee, filters))

	query = (
		frappe.qb.from_(Attendance)
		.select(
			Attendance.employee,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.status,
			Attendance.shift,
			Attendance.holiday_list,
			Attendance.docstatus,
		)
		.where(
			# (Attendance.docstatus == 1)
			(Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
			& Attendance.employee.isin(employee_subquery)
		)
	)

	if filters.employee:
		if isinstance(filters.employee, str):
			filters.employee = [filters.employee]
		query = query.where(Attendance.employee.isin(filters.employee))
	query = query.orderby(Attendance.employee, Attendance.attendance_date)
		

	return query.run(as_dict=1)


def get_employee_related_details(filters: Filters) -> Tuple[Dict, List]:
    """Returns
    1. nested dict for employee details
    2. list of values for the group by filter
    """
    Employee = frappe.qb.DocType("Employee")
    
    query = (
        frappe.qb.from_(Employee)
        .select(
            Employee.name,
            Employee.employee_name,
            Employee.designation,
            Employee.grade,
            Employee.department,
            Employee.branch,
            Employee.company,
            Employee.holiday_list,
            Employee.status,
            Employee.relieving_date,
            Employee.default_shift,
        )
        .where(Employee.company == filters.company)
    )


    # Use filters.get("is_active") for consistency
    if filters.get("department"):
        query = query.where(Employee.department == filters.department)
    query = query.where(get_active_or_recently_relieved_condition(Employee, filters))
    if filters.employee:
        if isinstance(filters.employee, str):
            filters.employee = [filters.employee]
        query = query.where(Employee.name.isin(filters.employee))
    group_by = filters.group_by
    if group_by:
        group_by = group_by.lower()
        query = query.orderby(group_by)

    employee_details = query.run(as_dict=True)

    group_by_param_values = []
    emp_map = {}

    if group_by:
        for parameter, employees in groupby(employee_details, key=lambda d: d[group_by]):
            group_by_param_values.append(parameter)
            emp_map.setdefault(parameter, frappe._dict())

            for emp in employees:
                emp_map[parameter][emp.name] = emp
    else:
        for emp in employee_details:
            emp_map[emp.name] = emp

    return emp_map, group_by_param_values


def get_holiday_map(filters: Filters) -> Dict[str, List[Dict]]:
	"""
	Returns a dict of holidays falling in the filter month and year
	with list name as key and list of holidays as values like
	{
	        'Holiday List 1': [
	                {'day_of_month': '0' , 'weekly_off': 1},
	                {'day_of_month': '1', 'weekly_off': 0}
	        ],
	        'Holiday List 2': [
	                {'day_of_month': '0' , 'weekly_off': 1},
	                {'day_of_month': '1', 'weekly_off': 0}
	        ]
	}
	"""
	# add default holiday list too
	holiday_lists = frappe.db.get_all("Holiday List", pluck="name")
	default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")
	holiday_lists.append(default_holiday_list)

	holiday_map = frappe._dict()
	Holiday = frappe.qb.DocType("Holiday")

	for d in holiday_lists:
		if not d:
			continue

		holidays = (
			frappe.qb.from_(Holiday)
			.select(Extract("day", Holiday.holiday_date).as_("day_of_month"), Holiday.weekly_off)
			.where(
				(Holiday.parent == d)
				& (Extract("month", Holiday.holiday_date) == filters.month)
				& (Extract("year", Holiday.holiday_date) == filters.year)
			)
		).run(as_dict=True)

		holiday_map.setdefault(d, holidays)

	return holiday_map

# MODIFIED: Added include_all parameter with default value of False
def get_rows(
	employee_details: Dict,
	filters: Filters,
	holiday_map: Dict,
	attendance_map: Dict,
	holiday_anchors: Dict,
	present_day_tags: Dict,
	include_all: bool = False,
) -> List[Dict]:
	records = []
	default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")
	shift_time_cache = {}

	for employee, details in employee_details.items():
		current_holiday_list = details.holiday_list or default_holiday_list
		holidays = holiday_map.get(current_holiday_list)

		is_inactive = details.get("status") and details.status != "Active"
		employee_display_name = (
			"{} ({})".format(details.employee_name, _("Inactive"))
			if filters.get("is_active") and is_inactive
			else details.employee_name
		)

		if filters.summarized_view:
			# MODIFIED: Added handling for employees with no attendance
			if employee not in attendance_map and include_all:
				# Create default row for employee with all absences
				total_days = get_total_days_in_month(filters)
				holiday_count = 0

				# Count holidays for this employee
				if holidays:
					holiday_count = len(holidays)

				row = {
					"employee": employee,
					"employee_name": employee_display_name,
					"total_present": 0.0,
					"total_leaves": 0.0,
					"total_absent": total_days - holiday_count,  # All days marked as absent except holidays
					"total_holidays": holiday_count,
					"unmarked_days": 0.0,
					"total_late_entries": 0.0,
					"total_early_exits": 0.0
				}

				set_defaults_for_summarized_view(filters, row)
				records.append(row)
				continue

			attendance = get_attendance_status_for_summarized_view(employee, filters, holidays)
			# MODIFIED: Only skip if attendance is empty and include_all is False
			if not attendance and not include_all:
				continue

			leave_summary = get_leave_summary(employee, filters)
			entry_exits_summary = get_entry_exits_summary(employee, filters)

			row = {"employee": employee, "employee_name": employee_display_name}
			set_defaults_for_summarized_view(filters, row)
			row.update(attendance)
			row.update(leave_summary)
			row.update(entry_exits_summary)

			records.append(row)
		else:
			employee_attendance = attendance_map.get(employee) or {}
			if not employee_attendance and not include_all:
				continue

			# One row per employee: each date's cell reflects that date's own
			# attendance status even if the employee had different shifts on
			# different days during the month.
			row = get_attendance_status_for_detailed_view(
				filters,
				employee_attendance,
				holiday_map,
				current_holiday_list,
				holiday_anchors.get(employee, []),
				present_day_tags.get(employee, {}),
				details.get("default_shift"),
				shift_time_cache,
			)
			row.update({"employee": employee, "employee_name": employee_display_name})
			records.append(row)

	return records


def set_defaults_for_summarized_view(filters, row):
	for entry in get_columns(filters):
		if entry.get("fieldtype") == "Float":
			row[entry.get("fieldname")] = 0.0


def get_attendance_status_for_summarized_view(
	employee: str, filters: Filters, holidays: List
) -> Dict:
	"""Returns dict of attendance status for employee like
	{'total_present': 1.5, 'total_leaves': 0.5, 'total_absent': 13.5, 'total_holidays': 8, 'unmarked_days': 5}
	"""
	summary, attendance_days = get_attendance_summary_and_days(employee, filters)
	if not any(summary.values()):
		return {}

	total_days = get_total_days_in_month(filters)
	total_holidays = total_unmarked_days = 0

	for day in range(1, total_days + 1):
		if day in attendance_days:
			continue

		status = get_holiday_status(day, holidays)
		if status in ["Weekly Off", "Holiday"]:
			total_holidays += 1
		elif not status:
			total_unmarked_days += 1

	return {
		"total_present": summary.total_present + summary.total_half_days,
		"total_leaves": summary.total_leaves + summary.total_half_days,
		"total_absent": summary.total_absent,
		"total_holidays": total_holidays,
		"unmarked_days": total_unmarked_days,
	}


def get_attendance_summary_and_days(employee: str, filters: Filters) -> Tuple[Dict, List]:
	Attendance = frappe.qb.DocType("Attendance")

	present_case = (
		frappe.qb.terms.Case()
		.when(((Attendance.status == "Present") | (Attendance.status == "Work From Home")), 1)
		.else_(0)
	)
	sum_present = Sum(present_case).as_("total_present")

	absent_case = frappe.qb.terms.Case().when(Attendance.status == "Absent", 1).else_(0)
	sum_absent = Sum(absent_case).as_("total_absent")

	leave_case = frappe.qb.terms.Case().when(Attendance.status == "On Leave", 1).else_(0)
	sum_leave = Sum(leave_case).as_("total_leaves")

	half_day_case = frappe.qb.terms.Case().when(Attendance.status == "Half Day", 0.5).else_(0)
	sum_half_day = Sum(half_day_case).as_("total_half_days")

	summary = (
		frappe.qb.from_(Attendance)
		.select(
			sum_present,
			sum_absent,
			sum_leave,
			sum_half_day,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.employee == employee)
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	).run(as_dict=True)

	days = (
		frappe.qb.from_(Attendance)
		.select(Extract("day", Attendance.attendance_date).as_("day_of_month"))
		.distinct()
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.employee == employee)
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	).run(pluck=True)

	return summary[0], days

# MODIFIED: Updated function to handle empty employee_attendance
def get_attendance_status_for_detailed_view(
	filters: Filters,
	employee_attendance: Dict,
	holiday_map: Dict,
	current_holiday_list: Optional[str],
	holiday_anchors: List[Tuple[int, str]],
	day_tags: Optional[Dict],
	current_shift: Optional[str],
	shift_time_cache: Dict,
) -> Dict:
	"""Returns a single date-wise attendance status row for the employee --
	one status per day regardless of how many shifts appear in their
	Attendance records that month. Days with no Attendance record fall back
	to Holiday/Weekly Off ("H/WO"): for days before today, resolved against
	the Holiday List of the closest later Attendance record (a gap right
	before a Holiday List change should still read as a day off); for
	today/future days, resolved against the employee's current Holiday List.
	"""
	total_days = get_total_days_in_month(filters)
	day_tags = day_tags or {}
	year = cint(filters.year)
	month = cint(filters.month)
	today = date.today()

	row = {"current_shift": get_shift_time_string(current_shift, shift_time_cache)}

	for day in range(1, total_days + 1):
		status = employee_attendance.get(day)

		if status is None:
			holiday_list_name = current_holiday_list
			if date(year, month, day) < today:
				for anchor_day, anchor_holiday_list in holiday_anchors:
					if anchor_day > day:
						holiday_list_name = anchor_holiday_list
						break
			status = get_holiday_status(day, holiday_map.get(holiday_list_name))

		if status is None:
			status = "Absent"

		abbr = status_map.get(status, "")
		if status == "Present" and day_tags.get(day):
			abbr = f"{abbr} ({day_tags[day]})"
		row[cstr(day)] = abbr

	return row


def get_shift_time_string(shift_name: Optional[str], cache: Dict) -> Optional[str]:
	if not shift_name:
		return None
	if shift_name not in cache:
		shift_time = frappe.db.get_value("Shift Type", shift_name, ["start_time", "end_time"])
		if shift_time and len(shift_time) == 2 and shift_time[0] and shift_time[1]:
			cache[shift_name] = "{} to {}".format(
				format_shift_time(shift_time[0]), format_shift_time(shift_time[1])
			)
		else:
			cache[shift_name] = None
	return cache[shift_name]


def format_shift_time(time_value) -> str:
	time_obj = datetime.strptime(str(time_value), "%H:%M:%S")
	return time_obj.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")


def get_holiday_status(day: int, holidays: List) -> str:
	status = None  # Changed from "Absent" to None to allow setting default outside
	if holidays:
		for holiday in holidays:
			if day == holiday.get("day_of_month"):
				if holiday.get("weekly_off"):
					status = "Weekly Off"
				else:
					status = "Holiday"
				break
	return status


def get_leave_summary(employee: str, filters: Filters) -> Dict[str, float]:
	"""Returns a dict of leave type and corresponding leaves taken by employee like:
	{'leave_without_pay': 1.0, 'sick_leave': 2.0}
	"""
	Attendance = frappe.qb.DocType("Attendance")
	day_case = frappe.qb.terms.Case().when(Attendance.status == "Half Day", 0.5).else_(1)
	sum_leave_days = Sum(day_case).as_("leave_days")

	leave_details = (
		frappe.qb.from_(Attendance)
		.select(Attendance.leave_type, sum_leave_days)
		.where(
			(Attendance.employee == employee)
			& (Attendance.docstatus == 1)
			& (Attendance.company == filters.company)
			& ((Attendance.leave_type.isnotnull()) | (Attendance.leave_type != ""))
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
		.groupby(Attendance.leave_type)
	).run(as_dict=True)

	leaves = {}
	for d in leave_details:
		leave_type = frappe.scrub(d.leave_type)
		leaves[leave_type] = d.leave_days

	return leaves


def get_entry_exits_summary(employee: str, filters: Filters) -> Dict[str, float]:
	"""Returns total late entries and total early exits for employee like:
	{'total_late_entries': 5, 'total_early_exits': 2}
	"""
	Attendance = frappe.qb.DocType("Attendance")

	late_entry_case = frappe.qb.terms.Case().when(Attendance.late_entry == "1", "1")
	count_late_entries = Count(late_entry_case).as_("total_late_entries")

	early_exit_case = frappe.qb.terms.Case().when(Attendance.early_exit == "1", "1")
	count_early_exits = Count(early_exit_case).as_("total_early_exits")

	entry_exits = (
		frappe.qb.from_(Attendance)
		.select(count_late_entries, count_early_exits)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.employee == employee)
			& (Attendance.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	).run(as_dict=True)

	return entry_exits[0]


@frappe.whitelist()
def get_attendance_years() -> str:
	"""Returns all the years for which attendance records exist"""
	Attendance = frappe.qb.DocType("Attendance")
	year_list = (
		frappe.qb.from_(Attendance)
		.select(Extract("year", Attendance.attendance_date).as_("year"))
		.distinct()
	).run(as_dict=True)

	if year_list:
		year_list.sort(key=lambda d: d.year, reverse=True)
	else:
		year_list = [frappe._dict({"year": getdate().year})]

	return "\n".join(cstr(entry.year) for entry in year_list)


def get_chart_data(attendance_map: Dict, filters: Filters) -> Dict:
	days = get_columns_for_days(filters)
	labels = []
	absent = []
	present = []
	leave = []