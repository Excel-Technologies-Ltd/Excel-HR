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

Filters = frappe._dict

status_map = {
	# "Half Day": "HD",
	"Holiday":"H",
	"Weekly Off": "WE",
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
        
    attendance_map = get_attendance_map(filters)
    
    columns = get_columns(filters)
    data = get_data(filters, attendance_map)

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
		columns.append({"label": _("Shift"), "fieldname": "shift", "fieldtype": "Data", "width": 120})
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


def get_data(filters: Filters, attendance_map: Dict) -> List[Dict]:
	employee_details, group_by_param_values = get_employee_related_details(filters)
	holiday_map = get_holiday_map(filters)
	data = []

	if filters.group_by:
		group_by_column = frappe.scrub(filters.group_by)

		for value in group_by_param_values:
			if not value:
				continue

			records = get_rows(employee_details[value], filters, holiday_map, attendance_map)

			if records:
				data.append({group_by_column: frappe.bold(value)})
				data.extend(records)
	else:
		data = get_rows(employee_details, filters, holiday_map, attendance_map)
	return data


def get_draft_requests(filters: Filters) -> Dict:
    """
    Query draft Leave Applications and Attendance Requests for the filter month and year.
    Returns a dictionary with two keys: 'leave_applications' and 'attendance_requests'.
    Each record contains the employee, start day, and end day of the draft request.
    """
    
    # Query draft Leave Applications
    LeaveApp = frappe.qb.DocType("Leave Application")
    Employee = frappe.qb.DocType("Employee")
    status_condition = (Employee.status == "Active") if filters.get("is_active") else (Employee.status != "Active")
    print("Filters: status_condition", status_condition)
    leave_apps = (
        frappe.qb.from_(LeaveApp)
        .join(Employee).on(Employee.name == LeaveApp.employee)
        .select(
            LeaveApp.employee,
            Employee.default_shift.as_("shift"),
            Extract("day", LeaveApp.from_date).as_("start_date"),
            Extract("day", LeaveApp.to_date).as_("to_date"),
            Extract("month", LeaveApp.from_date).as_("start_month"),
            Extract("month", LeaveApp.to_date).as_("to_month"),
        )
        .where(
            (LeaveApp.docstatus == 0) &
            (LeaveApp.status == "Open") &
            (LeaveApp.company == filters.company) &
            (
                (Extract("month", LeaveApp.from_date) == filters.month) |
                (Extract("month", LeaveApp.to_date) == filters.month)
            ) &
            (
                (Extract("year", LeaveApp.from_date) == filters.year) |
                (Extract("year", LeaveApp.to_date) == filters.year)
            )
            & (status_condition)
           
        )
    ).run(as_dict=True)

    # Query draft Attendance Requests
    AttendanceRequest = frappe.qb.DocType("Attendance Request")
    att_requests = (
        frappe.qb.from_(AttendanceRequest)
        .join(Employee).on(Employee.name == AttendanceRequest.employee)
        .select(
            AttendanceRequest.employee,
            AttendanceRequest.excel_shift.as_("shift"),
            Extract("day", AttendanceRequest.from_date).as_("start_date"),
            Extract("day", AttendanceRequest.to_date).as_("to_date"),
            Extract("month", AttendanceRequest.from_date).as_("start_month"),
            Extract("month", AttendanceRequest.to_date).as_("to_month"),
        )
        .where(
            (AttendanceRequest.docstatus == 0) &
            (AttendanceRequest.workflow_state == "Applied") &
            (AttendanceRequest.company == filters.company) &
            (
                (Extract("month", AttendanceRequest.from_date) == filters.month) |
                (Extract("month", AttendanceRequest.to_date) == filters.month)
            ) &
            (
                (Extract("year", AttendanceRequest.from_date) == filters.year) |
                (Extract("year", AttendanceRequest.to_date) == filters.year)
            )
            & (status_condition)
        )
    ).run(as_dict=True)

    return {
        "leave_applications": leave_apps,
        "attendance_requests": att_requests
    }


def get_attendance_map(filters: Filters) -> Dict:
    """Returns a dictionary of employee-wise attendance map as per shifts for all the days of the month."""
     
    attendance_list = get_attendance_records(filters)
    attendance_map = {}
    leave_map = {}
    
    # Get all employees first to ensure we have entries even for employees with no attendance
    employee_details, _ = get_employee_related_details(filters)
    all_employees = []
    
    if isinstance(employee_details, dict):
        # If employee_details is grouped by some parameter
        for param, emp_dict in employee_details.items():
            all_employees.extend(list(emp_dict.keys()))
    else:
        # If employee_details is a flat dict with employee names as keys
        all_employees = list(employee_details.keys())
    
    # Initialize attendance map for all employees with default shifts
    for employee in all_employees:
        # Get default shift for the employee
        default_shift = frappe.db.get_value("Employee", employee, "default_shift") or "General Shift-1"
        attendance_map.setdefault(employee, {}).setdefault(default_shift, {})
        
        # Mark all days as "Absent" by default
        for day in range(1, get_total_days_in_month(filters) + 1):
            attendance_map[employee][default_shift][day] = "Absent"
    
    # Now update with actual attendance records
    for d in attendance_list:
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
        attendance_map.setdefault(d.employee, {}).setdefault(d.shift, {})
        attendance_map[d.employee][d.shift][d.day_of_month] = status
    
    # Process draft requests
    draft_data = get_draft_requests(filters)
    
    for lr in draft_data.get("leave_applications", []):
        if lr.start_date is None or lr.to_date is None:
            continue
        if lr.start_month == lr.to_month:
            for day in range(lr.start_date, lr.to_date + 1):
                attendance_map.setdefault(lr.employee, {}).setdefault(lr.shift, {})
                attendance_map[lr.employee][lr.shift][day] = "Leave Application"
        else:
            if int(filters.month) == int(lr.start_month):
                for day in range(lr.start_date, get_total_days_in_month(filters) + 1):
                    attendance_map.setdefault(lr.employee, {}).setdefault(lr.shift, {})
                    attendance_map[lr.employee][lr.shift][day] = "Leave Application"
            elif int(filters.month) == int(lr.to_month):
                for day in range(1, lr.to_date + 1):
                    attendance_map.setdefault(lr.employee, {}).setdefault(lr.shift, {})
                    attendance_map[lr.employee][lr.shift][day] = "Leave Application"
    
    for ar in draft_data.get("attendance_requests", []):
        if ar.start_date is None or ar.to_date is None:
            continue
        if ar.start_month == ar.to_month:
            for day in range(ar.start_date, ar.to_date + 1):
                attendance_map.setdefault(ar.employee, {}).setdefault(ar.shift, {})
                attendance_map[ar.employee][ar.shift][day] = "Attendance Request"
        else:
            if int(filters.month) == int(ar.start_month):
                for day in range(ar.start_date, get_total_days_in_month(filters) + 1):
                    attendance_map.setdefault(ar.employee, {}).setdefault(ar.shift, {})
                    attendance_map[ar.employee][ar.shift][day] = "Attendance Request"
            elif int(filters.month) == int(ar.to_month):
                for day in range(1, ar.to_date + 1):
                    attendance_map.setdefault(ar.employee, {}).setdefault(ar.shift, {})
                    attendance_map[ar.employee][ar.shift][day] = "Attendance Request"
    
    # Now check for holiday/weekly off status and override Absent with appropriate status
    holiday_map = get_holiday_map(filters)
    
    for employee in all_employees:
        emp_holiday_list = frappe.db.get_value("Employee", employee, "holiday_list") or frappe.get_cached_value("Company", filters.company, "default_holiday_list")
        holidays = holiday_map.get(emp_holiday_list, [])
        
        for shift in attendance_map.get(employee, {}).keys():
            for day in range(1, get_total_days_in_month(filters) + 1):
                # Only override if it's currently set to Absent
                if attendance_map[employee][shift].get(day) == "Absent":
                    holiday_status = get_holiday_status(day, holidays)
                    if holiday_status:
                        attendance_map[employee][shift][day] = holiday_status
    
    return attendance_map




from datetime import datetime

def get_attendance_records(filters: Filters) -> List[Dict]:
    conditions = ""
    if filters.get("is_active"):
        conditions += " AND status = 'Active'"
    else:
        conditions += " AND status != 'Active'"
    sql_query =f"""
        SELECT
            employee,
            EXTRACT(day FROM attendance_date) AS day_of_month,
            status,
            late_entry,
            shift,
            attendance_request,
            leave_application
        FROM
            tabAttendance
        WHERE
            docstatus = 1
            AND company = %(company)s
           	AND EXTRACT(year FROM attendance_date) = %(year)s
            AND EXTRACT(month FROM attendance_date) = %(month)s
            {conditions}
        ORDER BY
            employee, attendance_date
    """

    # Assuming filters is a dictionary
    params = {
        "company": filters.company,
        "year": filters.year,
        "month": filters.month,
    }

    # Execute the SQL query and fetch results from the database
    results = frappe.db.sql(sql_query, params, as_dict=True)
    print({"records":get_attendance_records})

    return results


def get_employee_related_details(filters: Filters) -> Tuple[Dict, List]:
    """Returns
    1. nested dict for employee details
    2. list of values for the group by filter
    """
    # Assuming Employee is the name of your table
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
            excel_department
        FROM
            `tabEmployee`
        WHERE
            company = '{filters.company}'
    """

    if filters.get("is_active"):
        sql_query += " AND status = 'Active'"
    else:
        sql_query += " AND status != 'Active'"
    if filters.employee:
        employee_list = "','".join(filters.employee)
        sql_query += f" AND employee IN ('{employee_list}')"

    if filters.excel_department:
        sql_query += f" AND excel_parent_department = '{filters.excel_department}'"

    if filters.excel_section:
        sql_query += f" AND excel_hr_section = '{filters.excel_section}'"

    if filters.excel_sub_section:
        sql_query += f" AND excel_hr_sub_section = '{filters.excel_sub_section}'"

    if filters.excel_job_location:
        sql_query += f" AND excel_job_location = '{filters.excel_job_location}'"
    if filters.excel_reporting_location:
        sql_query += f" AND excel_reporting_location = '{filters.excel_reporting_location}'"    

    group_by = filters.group_by
    if group_by:
        group_by = group_by.lower()
        sql_query += f" ORDER BY {group_by}"

    # Assuming your database connection object is `db`
    employee_details = frappe.db.sql(sql_query, as_dict=True)

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


def get_rows(
    employee_details: Dict, filters: Filters, holiday_map: Dict, attendance_map: Dict
) -> List[Dict]:
    records = []
    default_holiday_list = frappe.get_cached_value("Company", filters.company, "default_holiday_list")

    for employee, details in employee_details.items():
        start_date = f"{filters.year}-{filters.month}-01"
        end_date = f"{filters.year}-{filters.month}-15"
        get_holiday = frappe.db.get_value("Attendance", {
            "attendance_date": ["between", [start_date, end_date]],
            "employee": employee,
            "status": ["in", ["Present", "Work From Home"]],
            "docstatus": 1
        }, ['holiday_list'], order_by="attendance_date ASC")
        
        emp_holiday_list = get_holiday or details.holiday_list or default_holiday_list
        holidays = holiday_map.get(emp_holiday_list, [])
        
        if filters.summarized_view:
            attendance = get_attendance_status_for_summarized_view(employee, filters, holidays)
            
            leave_summary = get_leave_summary(employee, filters)
            entry_exits_summary = get_entry_exits_summary(employee, filters)

            row = {"employee": employee, "employee_name": details.employee_name, 'department_name': details.department}
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
            # For detailed view, ensure employee appears even with no attendance
            if employee not in attendance_map:
                default_shift = frappe.db.get_value("Employee", employee, "default_shift") or "General Shift-1"
                attendance_map[employee] = {default_shift: {}}
                
                # Mark all days as absent by default
                for day in range(1, get_total_days_in_month(filters) + 1):
                    holiday_status = get_holiday_status(day, holidays)
                    attendance_map[employee][default_shift][day] = holiday_status if holiday_status else "Absent"
            
            employee_attendance = attendance_map.get(employee, {})
            attendance_for_employee = get_attendance_status_for_detailed_view(
                employee, filters, employee_attendance, holidays
            )
            
            # Set employee details in the first row
            attendance_for_employee[0].update(
                {"employee": employee, "employee_name": details.employee_name, 'department_name': details.department}
            )

            records.extend(attendance_for_employee)

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
	frappe.msgprint(frappe.as_json(holidays))
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
    employee: str, filters: Filters, employee_attendance: Dict, holidays: List
) -> List[Dict]:
    """Returns list of shift-wise attendance status for employee"""
    attendance_values = []
    total_days = get_total_days_in_month(filters)

    for shift, status_dict in employee_attendance.items():
        row = {"shift": shift}

        for day in range(1, total_days + 1):
            status = status_dict.get(day, "Absent")  # Default to Absent if no status
            
            # Only check for holiday status if current status is Absent
            if status == "Absent" and holidays:
                holiday_status = get_holiday_status(day, holidays)
                if holiday_status:
                    status = holiday_status

            abbr = status_map.get(status, "A")  # Default to "A" for Absent if no mapping
            color = get_color_for_status(status)
            
            row[day] = f'<span style="color: {color};">{abbr}</span>'

        attendance_values.append(row)

    return attendance_values




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
	status = "Absent"
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
     