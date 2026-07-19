# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


from calendar import monthrange
from itertools import groupby
from typing import Dict, List, Optional, Tuple
import re
import frappe
from frappe import _
from frappe.query_builder.functions import Count, Extract, Sum
from frappe.utils import cint, cstr, getdate
from typing import Dict
from datetime import datetime, date
from excel_hr.excel_hr.report.attendance_checkin_utils import get_local_checkin_tags, local_tag

Filters = frappe._dict

status_map = {
	# "Half Day": "HD",
	"Holiday":"H",
	"Weekly Off": "WO",
#  green
 	"Present": "P",
	"Present GS-1":"P.GS1",
	"Present GS-2":"P.GS2",
	"Present GS-3":"P.GS3",
 	"Present GS-4":"P.GS4",
	"Present GS-5":"P.GS5",
	"Present GS-6":"P.GS6",
	"Late Attendance GS-1":"L.GS1",
	"Late Attendance GS-2":"L.GS2",
	"Late Attendance GS-3":"L.GS3",
 	"Late Attendance GS-4":"L.GS4",
	"Late Attendance GS-5":"L.GS5",
	"Late Attendance GS-6":"L.GS6",
 	"Work From Home": "WFH",
	"Off Day Duty GS-1":"O.GS1",
	"Off Day Duty GS-2":"O.GS2",
	"Off Day Duty GS-3":"O.GS3",
 	"Off Day Duty GS-4":"O.GS4",
	"Off Day Duty GS-5":"O.GS5",
	"Off Day Duty GS-6":"O.GS6",
 	"Outside Duty GS-1":"OW.GS1",
  	"Outside Duty GS-2":"OW.GS2",
   	"Outside Duty GS-3":"OW.GS3",
 	"Outside Duty GS-4":"OW.GS4",
  	"Outside Duty GS-5":"OW.GS5",
   	"Outside Duty GS-6":"OW.GS6",    
    "Foreign Tour":"P.FT",
	"Local Tour":"P.LT",
 	
#   blue
  	"Absent": "A",
	"On Leave": "L",
    "Annual Leave":"AL",
    "Annual Casual Leave":"L.AC",
    "Annual Medical Leave":"L.AM",
	"Special Leave":"L.SP",
 	"Special Casual Leave":"L.SC",
    "Special Medical Leave":"L.SM",
	"Monthly Paid Leave":"L.MP",
    "Compensatory Leave":"L.AD",
    "Leave Without Pay" :"LWP",
    "Maternity Leave":"L.MT",
    "Leave Application":"L.App",
    "Attendance Request":"A.App"
#  red
}

day_abbr = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def execute(filters: Optional[Filters] = None) -> Tuple:
    filters = frappe._dict(filters or {})
        
    attendance_map, holiday_anchors = get_attendance_map(filters)
    present_day_tags = get_present_day_tags(filters)

    columns = get_columns(filters)
    data = get_data(filters, attendance_map, holiday_anchors, present_day_tags)

    if not data:
        frappe.msgprint(
            _("No employees found for this criteria."), alert=True, indicator="orange"
        )
        return columns, [], None, None

    message = get_message() if filters.show_abbr else ""
    # chart = get_chart_data(attendance_map, filters)

    return columns, data, message


def get_message() -> str:
    message = ""
    colors_group1 = [
        "green", "red", "orange", "blue", "#318AD8",
        "lightgray", "green", "green", "green", "green"
    ]

    colors_group2 = [
        "green", "green", "green", "green", "green",
        "green", "green", "green", "purple", "brown",
        "blue", "blue", "blue", "blue", "blue",
        "blue", "blue", "blue", "blue", "blue"
    ]

    colors_group3 = [
        "green", "green", "green", "green", "green",
        "green", "green", "green", "purple", "brown",
        "blue", "blue", "blue", "blue", "blue",
        "blue", "blue", "blue", "blue", "blue"
    ]

    count = 0

    # Start the row
    message += "<div style='display: flex;height:30vh'>"

    # First column
    message += "<div style='flex: 1;'>"
    for (status, abbr), color in zip(list(status_map.items())[:2], colors_group1):
        message += f"""
            <span style='font-size:10px;color:black; padding-right: 12px; padding-left: 5px; margin-right: 3px; display: block;'>
                	&#8718; {status} - {abbr}
            </span>
        """
        count += 1
    message += "</div>"

    # Second column
    message += "<div style='flex: 1; '>"
    count = 0
    for (status, abbr), color in zip(list(status_map.items())[2:16], colors_group2):
        message += f"""
            <span style='font-size:10px; color:blue; padding-right: 12px; padding-left: 5px; margin-right: 3px; display: block;'>
                &#8718; {status} - {abbr}
            </span>
        """
        count += 1
    message += "</div>"

    # Third column
    message += "<div style='flex: 1;'>"
    count = 0
    for (status, abbr), color in zip(list(status_map.items())[16:30], colors_group3):
        message += f"""
            <span style='font-size:10px; color:blue; padding-right: 12px; padding-left: 5px; margin-right: 3px; display: block;'>
                &#8718; {status} - {abbr}
            </span>
        """
        count += 1
    message += "</div>"
    # Fourth column
    message += "<div style='flex: 1;'>"
    count = 0
    message +="<h1 style='font-size:10px; color:red;'> **N.B: Empty cells signify Absence.</h1>"
    for (status, abbr), color in zip(list(status_map.items())[30:], colors_group3):
        message += f"""
            <span style='font-size:10px; color:red; padding-right: 12px; padding-left: 5px; margin-right: 3px; display: block;'>
                &#8718; {status} - {abbr}
            </span>
            
        """
        count += 1
    message += "</div>"    
    # Fifth column
    # message += "<div style='flex: 1;'>"
    # count = 0
    # for (status, abbr), color in zip(list(status_map.items())[36:46], colors_group3):
    #     message += f"""
    #         <span style='font-size:10px; color:red; padding-right: 12px; padding-left: 5px; margin-right: 3px; display: block;'>
    #             &#8718; {status} - {abbr}
    #         </span>
    #     """
    #     count += 1
    # message += "</div>"  
         

    # End the row
    message += "</div>"

    return message




def get_columns(filters: Filters) -> List[Dict]:
	columns = []

	if filters.group_by:
		columns.append(
			{
				"label": _(filters.group_by),
				"fieldname": frappe.scrub(filters.group_by),
				"fieldtype": "Link",
				"options": "Branch",
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
			{"label": _("Department"), "fieldname": "department_name", "fieldtype": "Data", "width": 120},
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
				# {
				# 	"label": _("Total Holidays"),
				# 	"fieldname": "total_holidays",
				# 	"fieldtype": "Float",
				# 	"width": 120,
				# },
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
		# forms the dates from selected year and month from filters
		date = "{}-{}-{}".format(cstr(filters.year), cstr(filters.month), cstr(day))
		# gets abbr from weekday number
		weekday = day_abbr[getdate(date).weekday()]
		# sets days as 1 Mon, 2 Tue, 3 Wed
		label = "{} {}".format(cstr(day), weekday)
		days.append({"label": label, "fieldtype": "Data", "fieldname": day, "width": 70})

	return days



def get_total_days_in_month(filters: Filters) -> int:
	return monthrange(cint(filters.year), cint(filters.month))[1]


def get_relieved_in_range_dates(filters: Filters) -> Tuple[str, str]:
	total_days = get_total_days_in_month(filters)
	month_start = "{}-{:02d}-01".format(cint(filters.year), cint(filters.month))
	month_end = "{}-{:02d}-{:02d}".format(cint(filters.year), cint(filters.month), total_days)
	return month_start, month_end


def get_active_or_recently_relieved_condition(Employee, filters: Filters):
	"""Query-builder version: Active employees, plus anyone relieved during
	the selected month, so their attendance still shows in the Active view
	instead of disappearing entirely."""
	if not filters.get("is_active"):
		return Employee.status != "Active"

	month_start, month_end = get_relieved_in_range_dates(filters)
	return (Employee.status == "Active") | (
		(Employee.relieving_date >= month_start) & (Employee.relieving_date <= month_end)
	)


def get_active_or_recently_relieved_sql(filters: Filters, alias: str = "") -> Tuple[str, Dict]:
	"""Raw-SQL version of the same condition: returns (sql_fragment, params)."""
	prefix = f"{alias}." if alias else ""
	if not filters.get("is_active"):
		return f"AND {prefix}status != 'Active'", {}

	month_start, month_end = get_relieved_in_range_dates(filters)
	return (
		f"AND ({prefix}status = 'Active' OR ({prefix}relieving_date BETWEEN %(rel_start)s AND %(rel_end)s))",
		{"rel_start": month_start, "rel_end": month_end},
	)


def get_data(filters: Filters, attendance_map: Dict, holiday_anchors: Dict, present_day_tags: Dict) -> List[Dict]:
	employee_details, group_by_param_values = get_employee_related_details(filters)
	holiday_map = get_holiday_map(filters)
	data = []

	if filters.group_by:
		group_by_column = frappe.scrub(filters.group_by)

		for value in group_by_param_values:
			if not value:
				continue

			records = get_rows(
				employee_details[value], filters, holiday_map, attendance_map, holiday_anchors, present_day_tags
			)

			if records:
				data.append({group_by_column: frappe.bold(value)})
				data.extend(records)
	else:
		data = get_rows(employee_details, filters, holiday_map, attendance_map, holiday_anchors, present_day_tags)
	return data


def get_present_day_tags(filters: Filters) -> Dict[str, Dict[int, str]]:
	"""For each employee/day marked Present (any shift's General Shift GS-1..GS-6
	variant is still stored as the base "Present" status on Attendance), work
	out the "RC" (Remote Checkin) tag to append to the abbreviation (e.g.
	"P.GS1") when the employee's IN and/or OUT checkin that day was made on
	the set_local device. Returns {employee: {day_of_month: tag}}."""
	Attendance = frappe.qb.DocType("Attendance")
	Employee = frappe.qb.DocType("Employee")

	query = (
		frappe.qb.from_(Attendance)
		.join(Employee).on(Employee.name == Attendance.employee)
		.select(
			Attendance.employee,
			Extract("day", Attendance.attendance_date).as_("day_of_month"),
			Attendance.attendance_date,
		)
		.where(
			(Attendance.docstatus == 1)
			& (Attendance.status == "Present")
			& (Employee.company == filters.company)
			& (Extract("month", Attendance.attendance_date) == filters.month)
			& (Extract("year", Attendance.attendance_date) == filters.year)
		)
	)
	query = query.where(get_active_or_recently_relieved_condition(Employee, filters))
	if filters.get("department"):
		query = query.where(Employee.department == filters.department)
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
		attendance_date = getdate(row.attendance_date)
		is_local_checkin = local_tag(checkin_tags, row.employee, attendance_date, "IN") or local_tag(
			checkin_tags, row.employee, attendance_date, "OUT"
		)
		tag = "RC" if is_local_checkin else None
		if tag:
			tags.setdefault(row.employee, {})[row.day_of_month] = tag

	return tags


def get_draft_requests(filters: Filters) -> Dict:
    # Status condition
    status_condition, status_params = get_active_or_recently_relieved_sql(filters, alias="emp")

    # Query draft Leave Applications
    leave_apps = frappe.db.sql(f"""
        SELECT
            la.employee,
            EXTRACT(day FROM la.from_date) as start_date,
            EXTRACT(day FROM la.to_date) as to_date,
            EXTRACT(month FROM la.from_date) as start_month,
            EXTRACT(month FROM la.to_date) as to_month
        FROM
            `tabLeave Application` la
        JOIN
            `tabEmployee` emp ON la.employee = emp.name
        WHERE
            la.docstatus = 0
            AND la.status = 'Open'
            AND la.company = %(company)s
            AND (
                EXTRACT(month FROM la.from_date) = %(month)s
                OR EXTRACT(month FROM la.to_date) = %(month)s
            )
            AND (
                EXTRACT(year FROM la.from_date) = %(year)s
                OR EXTRACT(year FROM la.to_date) = %(year)s
            )
            {status_condition}
    """, {
        "company": filters.company,
        "month": filters.month,
        "year": filters.year,
        **status_params,
    }, as_dict=True)

    # Query draft Attendance Requests
    att_requests = frappe.db.sql(f"""
        SELECT
            ar.employee,
            EXTRACT(day FROM ar.from_date) as start_date,
            EXTRACT(day FROM ar.to_date) as to_date,
            EXTRACT(month FROM ar.from_date) as start_month,
            EXTRACT(month FROM ar.to_date) as to_month
        FROM
            `tabAttendance Request` ar
        JOIN
            `tabEmployee` emp ON ar.employee = emp.name
        WHERE
            ar.docstatus = 0
            AND ar.workflow_state = 'Applied'
            AND ar.company = %(company)s
            AND (
                EXTRACT(month FROM ar.from_date) = %(month)s
                OR EXTRACT(month FROM ar.to_date) = %(month)s
            )
            AND (
                EXTRACT(year FROM ar.from_date) = %(year)s
                OR EXTRACT(year FROM ar.to_date) = %(year)s
            )
            {status_condition}
    """, {
        "company": filters.company,
        "month": filters.month,
        "year": filters.year,
        **status_params,
    }, as_dict=True)

    return {
        "leave_applications": leave_apps,
        "attendance_requests": att_requests
    }

def get_attendance_map(filters: Filters) -> Tuple[Dict, Dict]:
    """Returns
    1. a dictionary of employee-wise, date-wise attendance status for the
       month (one status per employee per day, even if the employee had
       different shifts on different days -- the GS-N shift is already
       baked into the status text itself, e.g. "Present GS-1")
    2. a dictionary of employee-wise list of (day_of_month, holiday_list)
       drawn from their actual Attendance records, sorted ascending by day --
       used to resolve which Holiday List was in effect around a gap in
       attendance.
    """
    attendance_list = get_attendance_records(filters)
    attendance_map = {}
    holiday_anchors = {}

    for d in attendance_list:
        if d.holiday_list:
            holiday_anchors.setdefault(d.employee, []).append((d.day_of_month, d.holiday_list))

        status = d.status
        # Handle status variations as in the original code
        if d.status == 'Present' and d.late_entry == 0:
            if d.attendance_request:
               data = frappe.db.get_value('Attendance Request', d.attendance_request, ['reason','excel_criteria_of_reason'])
               if data:
                  reason = data[0]
                  criteria = data[1] 
               if reason == 'On Duty' and criteria == 'Foreign Tour':
                   status = 'Foreign Tour'
               elif reason == 'On Duty' and criteria == 'Local Tour':
                   status = 'Local Tour'
               elif reason == 'On Duty' and criteria == 'Off Day Duty':
                   if d.shift == "General Shift-1":
                       status = "Off Day Duty GS-1" 
                   elif d.shift == "General Shift-2":
                        status = "Off Day Duty GS-2"
                   elif d.shift == "General Shift-3":
                       status = "Off Day Duty GS-3"
                   elif d.shift == "General Shift-4":
                       status = "Off Day Duty GS-4"
                   elif d.shift == "General Shift-5":
                       status = "Off Day Duty GS-5"
                   elif d.shift == "General Shift-6":
                       status = "Off Day Duty GS-6"                                                                     
               elif reason == 'On Duty':
                   if d.shift == "General Shift-1":
                       status = "Outside Duty GS-1"
                   elif d.shift == "General Shift-2":
                       status = "Outside Duty GS-2"
                   elif d.shift == "General Shift-3":
                       status = "Outside Duty GS-3"  
                   elif d.shift == "General Shift-4":
                       status = "Outside Duty GS-4" 
                   elif d.shift == "General Shift-5":
                       status = "Outside Duty GS-5" 
                   elif d.shift == "General Shift-6":
                       status = "Outside Duty GS-6"                                                                           
            elif d.shift == "General Shift-1":
                status = "Present GS-1"
            elif d.shift == "General Shift-2":
                status = "Present GS-2" 
            elif d.shift == "General Shift-3":
                status = "Present GS-3"   
            elif d.shift == "General Shift-4":
                status = "Present GS-4"   
            elif d.shift == "General Shift-5":
                status = "Present GS-5"   
            elif d.shift == "General Shift-6":
                status = "Present GS-6"                                                   
        elif d.status == 'Present' and d.late_entry == 1: 
            if d.shift == "General Shift-1":
                status = "Late Attendance GS-1"
            elif d.shift == "General Shift-2":
                status = "Late Attendance GS-2" 
            elif d.shift == "General Shift-3":
                status = "Late Attendance GS-3" 
            elif d.shift == "General Shift-4":
                status = "Late Attendance GS-4"  
            elif d.shift == "General Shift-5":
                status = "Late Attendance GS-5"  
            elif d.shift == "General Shift-6":
                status = "Late Attendance GS-6"                                                            	
        elif d.status == "On Leave":
            data = frappe.db.get_value('Leave Application', d.leave_application, ['leave_type','excel_leave_category'])
            if not data:
                status = "On Leave"
            else:
                leave_type = data[0]
                leave_category = data[1]
                if leave_type == "Special Leave" and leave_category == "Casual":
                    status = 'Special Casual Leave'
                elif leave_type == "Special Leave" and leave_category == "Medical":
                    status = "Special Medical Leave"
                elif leave_type == "Special Leave":
                    status = "Special Leave" 
                elif leave_type == "Monthly Paid Leave":
                    status = "Monthly Paid Leave"
                elif leave_type == "Annual Leave" and leave_category == "Casual":
                    status = "Annual Casual Leave"
                elif leave_type == "Annual Leave" and leave_category == "Medical":
                    status = "Annual Medical Leave"
                elif leave_type == "Annual Leave":
                    status = "Annual Leave"
                elif leave_type == "Compensatory Leave":
                    status = "Compensatory Leave"  
                elif leave_type == "Leave Without Pay":
                    status = "Leave Without Pay"
                elif leave_type == "Maternity Leave":
                    status = "Maternity Leave"                                                                                                
        
        # Update attendance map with actual attendance status
        attendance_map.setdefault(d.employee, {})[d.day_of_month] = status

    # Process draft requests
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

    # Holiday/Weekly Off resolution for days with no attendance record is done
    # per-day, at read time, in get_attendance_status_for_detailed_view -- see
    # holiday_anchors below (day-of-month vs the Holiday List that was in
    # effect around that gap).
    for employee in holiday_anchors:
        holiday_anchors[employee].sort(key=lambda entry: entry[0])

    return attendance_map, holiday_anchors


def get_attendance_records(filters: Filters) -> List[Dict]:
    active_condition, active_params = get_active_or_recently_relieved_sql(filters, alias="emp")
    conditions = " " + active_condition

    if filters.get("employee"):
        if isinstance(filters.employee, list):
            employee_placeholders = ", ".join([f"%({f'emp_{i}'})s" for i in range(len(filters.employee))])
            conditions += f" AND att.employee IN ({employee_placeholders})"
        else:
            conditions += " AND att.employee = %(employee)s"

    sql_query = f"""
        SELECT
            att.employee,
            EXTRACT(day FROM att.attendance_date) AS day_of_month,
            att.status,
            att.late_entry,
            att.shift,
            att.holiday_list,
            att.attendance_request,
            att.leave_application
        FROM
            `tabAttendance` att
        JOIN
            `tabEmployee` emp ON att.employee = emp.name
        WHERE
            att.docstatus = 1
            AND att.company = %(company)s
            AND EXTRACT(year FROM att.attendance_date) = %(year)s
            AND EXTRACT(month FROM att.attendance_date) = %(month)s
            {conditions}
        ORDER BY
            att.employee, att.attendance_date
    """

    params = {
        "company": filters.company,
        "year": filters.year,
        "month": filters.month,
        **active_params,
    }

    if filters.get("employee"):
        if isinstance(filters.employee, list):
            for i, emp_id in enumerate(filters.employee):
                params[f"emp_{i}"] = emp_id
        else:
            params["employee"] = filters.employee

    return frappe.db.sql(sql_query, params, as_dict=True)


def get_employee_related_details(filters: Filters) -> Tuple[Dict, List]:
    active_condition, active_params = get_active_or_recently_relieved_sql(filters)
    conditions = " " + active_condition

    sql_query = f"""
        SELECT
            name,
            employee_name,
            designation,
            grade,
            department,
            branch,
            company,
            holiday_list,
            excel_department,
            status,
            relieving_date,
            default_shift,
            date_of_joining
        FROM
            `tabEmployee`
        WHERE
            company = %(company)s
            {conditions}
    """

    if filters.employee:
        if isinstance(filters.employee, list):
            employee_list = "','".join(filters.employee)
            sql_query += f" AND name IN ('{employee_list}')"
        else:
            sql_query += " AND name = %(employee)s"

    # Rest of your existing conditions...
    if filters.excel_department:
        sql_query += f" AND excel_parent_department = '{filters.excel_department}'"

    if filters.excel_section:
        sql_query += f" AND excel_hr_section = '{filters.excel_section}'"

    if filters.excel_sub_section:
        sql_query += f" AND excel_hr_sub_section = '{filters.excel_sub_section}'"

    if filters.custom_job_location:
        sql_query += f" AND custom_job_location = '{filters.custom_job_location}'"
    if filters.custom_reporting_location:
        sql_query += f" AND custom_reporting_location = '{filters.custom_reporting_location}'"    

    group_by = filters.group_by
    if group_by:
        group_by = group_by.lower()
        sql_query += f" ORDER BY {group_by}"

    params = {
        "company": filters.company,
        **active_params,
    }

    if filters.employee and not isinstance(filters.employee, list):
        params["employee"] = filters.employee

    employee_details = frappe.db.sql(sql_query, params, as_dict=True)

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


# here need to change

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


def get_work_history_map(employee_names: List[str]) -> Dict[str, List[Dict]]:
	"""Returns {employee: [Internal Work History rows]} for the given employees."""
	if not employee_names:
		return {}

	rows = frappe.get_all(
		"Employee Internal Work History",
		filters={"parent": ["in", employee_names], "parenttype": "Employee"},
		fields=["parent", "from_date", "to_date", "custom_holiday_list"],
		order_by="parent asc, from_date asc",
	)

	work_history_map = {}
	for row in rows:
		work_history_map.setdefault(row.parent, []).append(row)
	return work_history_map


def find_work_history_holiday_list(current_date, work_history_rows, date_of_joining):
	"""Returns the custom_holiday_list from the Internal Work History row whose
	[from_date, to_date] period covers current_date, if any. A row with no
	from_date is treated as starting on the employee's date_of_joining; a row
	with no to_date is treated as still open."""
	for row in work_history_rows or []:
		value = row.get("custom_holiday_list")
		if not value:
			continue

		from_date = row.get("from_date") or date_of_joining
		if not from_date:
			continue
		from_date = getdate(from_date)

		to_date = row.get("to_date")
		if to_date and current_date > getdate(to_date):
			continue
		if current_date < from_date:
			continue

		return value

	return None


def get_rows(
    employee_details: Dict,
    filters: Filters,
    holiday_map: Dict,
    attendance_map: Dict,
    holiday_anchors: Dict,
    present_day_tags: Dict,
) -> List[Dict]:
    records = []
    default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")
    shift_time_cache = {}
    work_history_map = get_work_history_map(list(employee_details.keys()))

    for employee, details in employee_details.items():
        current_holiday_list = details.holiday_list or default_holiday_list
        holidays = holiday_map.get(current_holiday_list, [])

        is_inactive = details.get("status") and details.status != "Active"
        employee_display_name = (
            "{} ({})".format(details.employee_name, _("Inactive"))
            if filters.get("is_active") and is_inactive
            else details.employee_name
        )

        if filters.summarized_view:
            attendance = get_attendance_status_for_summarized_view(employee, filters, holidays)

            leave_summary = get_leave_summary(employee, filters)
            entry_exits_summary = get_entry_exits_summary(employee, filters)

            row = {"employee": employee, "employee_name": employee_display_name, 'department_name': details.department}
            set_defaults_for_summarized_view(filters, row)

            # If no attendance data, set all days as absent
            if not attendance:
                total_days = get_total_days_in_month(filters)
                total_holidays = sum(1 for day in range(1, total_days + 1)
                                    if get_holiday_status(day, holidays) in ["Weekly Off", "Holiday"])

                attendance = {
                    "total_present": 0,
                    "total_leaves": 0,
                    "total_absent": total_days - total_holidays,
                    "total_holidays": total_holidays,
                    "unmarked_days": 0,
                }

            row.update(attendance)
            row.update(leave_summary)
            row.update(entry_exits_summary)

            records.append(row)
        else:
            # One row per employee: each date's cell reflects that date's own
            # attendance status even if the employee had different shifts on
            # different days during the month.
            employee_attendance = attendance_map.get(employee) or {}
            row = get_attendance_status_for_detailed_view(
                filters,
                employee_attendance,
                holiday_map,
                current_holiday_list,
                holiday_anchors.get(employee, []),
                present_day_tags.get(employee, {}),
                details.get("default_shift"),
                shift_time_cache,
                work_history_map.get(employee, []),
                details.get("date_of_joining"),
            )
            row.update(
                {"employee": employee, "employee_name": employee_display_name, 'department_name': details.department}
            )
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


# def get_attendance_status_for_detailed_view(
# 	employee: str, filters: Filters, employee_attendance: Dict, holidays: List
# ) -> List[Dict]:
# 	"""Returns list of shift-wise attendance status for employee
# 	[
# 	        {'shift': 'Morning Shift', 1: 'A', 2: 'P', 3: 'A'....},
# 	        {'shift': 'Evening Shift', 1: 'P', 2: 'A', 3: 'P'....}
# 	]
# 	"""
# 	total_days = get_total_days_in_month(filters)
# 	attendance_values = []

# 	for shift, status_dict in employee_attendance.items():
# 		row = {"shift": shift}

# 		for day in range(1, total_days + 1):
# 			status = status_dict.get(day)
# 			if status is None and holidays:
# 				status = get_holiday_status(day, holidays)

# 			abbr = status_map.get(status, "")
# 			row[day] = abbr

# 		attendance_values.append(row)

# 	return attendance_values

def get_attendance_status_for_detailed_view(
    filters: Filters,
    employee_attendance: Dict,
    holiday_map: Dict,
    current_holiday_list: Optional[str],
    holiday_anchors: List[Tuple[int, str]],
    day_tags: Optional[Dict],
    current_shift: Optional[str],
    shift_time_cache: Dict,
    work_history_rows: Optional[List[Dict]] = None,
    date_of_joining=None,
) -> Dict:
    """Returns a single date-wise attendance status row for the employee --
    one status per day regardless of how many shifts appear in their
    Attendance records that month (the GS-N shift is already baked into the
    status text, e.g. "Present GS-1"). Days with no Attendance record fall
    back to Holiday ("H") or Weekly Off ("WO"), resolved for days before today in
    this order: 1st, the employee's own Internal Work History for that date
    (e.g. an Employee Transfer changed their Holiday List and this gap day
    falls in that period); 2nd, the Holiday List of the closest later
    Attendance record (a gap right before a Holiday List change should still
    read as a day off). Today/future days are resolved against the
    employee's current Holiday List.
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
                wh_holiday_list = find_work_history_holiday_list(
                    date(year, month, day), work_history_rows, date_of_joining
                )
                if wh_holiday_list:
                    holiday_list_name = wh_holiday_list
                else:
                    for anchor_day, anchor_holiday_list in holiday_anchors:
                        if anchor_day > day:
                            holiday_list_name = anchor_holiday_list
                            break
            status = get_holiday_status(day, holiday_map.get(holiday_list_name, []))

        if status is None:
            status = "Absent"

        abbr = status_map.get(status, "A")  # Default to "A" for Absent if no mapping
        color = get_color_for_status(status)

        if status.startswith("Present") and day_tags.get(day):
            abbr = f"{abbr} ({day_tags[day]})"

        row[day] = f'<span style="color: {color};">{abbr}</span>'

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




def get_color_for_status(status: str) -> str:
    if status in ("Absent", "On Leave", "Annual Leave", "Compensatory Leave", "Leave Without Pay", "Maternity Leave", 
                 "Annual Casual Leave", "Annual Medical Leave", "Special Leave", "Special Casual Leave", 
                 "Special Medical Leave", "Monthly Paid Leave", "Leave Application", "Attendance Request"):
        return "red"
    elif status in ("Holiday", "Weekly Off"):
        return "black"
    elif status in ("Present", "Present GS-1", "Present GS-2", "Present GS-3", "Present GS-4", "Present GS-5", 
                   "Present GS-6", "Late Attendance GS-1", "Late Attendance GS-2", "Late Attendance GS-3", 
                   "Late Attendance GS-4", "Late Attendance GS-5", "Late Attendance GS-6", "Off Day Duty GS-1", 
                   "Off Day Duty GS-2", "Off Day Duty GS-3", "Off Day Duty GS-4", "Off Day Duty GS-5", 
                   "Off Day Duty GS-6", "Outside Duty GS-1", "Outside Duty GS-2", "Outside Duty GS-3", 
                   "Outside Duty GS-4", "Outside Duty GS-5", "Outside Duty GS-6", "Foreign Tour", "Local Tour", 
                   "Work From Home"):
        return "blue"
    else:
        return "black"  # Default color


def get_holiday_status(day: int, holidays: List) -> str:
    """Returns holiday status only if there's no attendance marked for that day"""
    status = None  # Default to None - meaning no holiday status
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

	for day in days:
		labels.append(day["label"])
		total_absent_on_day = total_leaves_on_day = total_present_on_day = 0

		for employee, attendance_dict in attendance_map.items():
			for shift, attendance in attendance_dict.items():
				attendance_on_day = attendance.get(day["fieldname"])

				if attendance_on_day == "On Leave":
					# leave should be counted only once for the entire day
					total_leaves_on_day += 1
					break
				elif attendance_on_day == "Absent":
					total_absent_on_day += 1
				elif attendance_on_day in ["Present", "Work From Home"]:
					total_present_on_day += 1
				elif attendance_on_day == "Half Day":
					total_present_on_day += 0.5
					total_leaves_on_day += 0.5

		absent.append(total_absent_on_day)
		present.append(total_present_on_day)
		leave.append(total_leaves_on_day)

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Absent", "values": absent},
				{"name": "Present", "values": present},
				{"name": "Leave", "values": leave},
			],
		},
		"type": "line",
		"colors": ["red", "green", "blue"],
	}
 
 
#  def get_holiday_status_from_attendance(name,):
     