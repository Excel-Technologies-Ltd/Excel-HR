import frappe
from datetime import datetime, timedelta
from frappe.query_builder.functions import Count, Extract, Sum
from typing import Dict, List, Optional, Tuple
Filters = frappe._dict

def execute(filters=None):
    if filters:
        validate_filters(filters)
    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def validate_filters(filters):
    """Validate that the date range falls within the selected month."""
    date_range = filters.get('date_range')
    
    if not date_range or len(date_range) != 2:
        frappe.throw("Please select a valid date range.")
    
    start_date_str, end_date_str = date_range[0], date_range[1]
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    month = int(filters.get('month'))
    year = int(filters.get('year'))
    
    if start_date.year != year or end_date.year != year:
        frappe.throw("The date range must be within the selected year.")
    
    if start_date > end_date:
        frappe.throw("The start date cannot be later than the end date.")

def get_columns(filters):
    columns = []
    columns.append({
        "label": "Employee ID",
        "fieldname": "employee_id",
        "fieldtype": "Link",
        "options": "Employee",
        "width": 120
    })

    date_range = filters.get("date_range")
    if not date_range or len(date_range) != 2:
        return columns
    
    start_date_str = date_range[0]
    end_date_str = date_range[1]
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%d-%b-%Y")
        columns.append({
            "label": f"(In Time) {date_str}",
            "fieldname": f"in_{current_date.day}",
            "fieldtype": "Data",
            "width": 130,
            "align": "center"
        })
        columns.append({
            "label": f"(Out Time) {date_str}",
            "fieldname": f"out_{current_date.day}",
            "fieldtype": "Data",
            "width": 130,
            "align": "center"
        })
        current_date += timedelta(days=1)
    return columns

def get_todays_checkins(employee_ids):
    """Fetch today's check-in records for employees"""
    today = datetime.now().strftime('%Y-%m-%d')
    checkins = frappe.get_all('Employee Checkin',
        filters={
            'employee': ['in', employee_ids],
            'time': ['between', [today + ' 00:00:00', today + ' 23:59:59']],
            'log_type': ['in', ['IN', 'OUT']]
        },
        fields=['employee', 'time', 'log_type'],
        order_by='employee,time'
    )
    
    checkin_dict = {}
    for checkin in checkins:
        employee = checkin['employee']
        if employee not in checkin_dict:
            checkin_dict[employee] = []
        checkin_dict[employee].append({
            'time': checkin['time'].strftime('%H:%M') if checkin['time'] else None,
            'type': checkin['log_type']
        })
    return checkin_dict

def get_data(filters):
    data = []
    employee_ids = []
    
    if not employee_ids or len(employee_ids) == 0:
        conditions = {}
        if filters.get('is_active'):
            conditions['status'] = 'Active'
        else:
            conditions['status'] = ['!=', 'Active']
        if filters.get('department'):
            conditions['department'] = filters.get('department')
        if filters.get('custom_job_location'):
            conditions['custom_job_location'] = filters.get('custom_job_location')
        if filters.get('custom_reporting_location'):
            conditions['custom_reporting_location'] = filters.get('custom_reporting_location')
        # if employee need in operator
        if filters.get('employee'):
            conditions['name'] = ['in', filters.get('employee')]
        employee_ids = frappe.get_all('Employee', filters=conditions, pluck='name')

    if not employee_ids:
        return data
    
    start_date_str = filters.get("date_range")[0]
    end_date_str = filters.get("date_range")[1]
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    today = datetime.now().date()
    
    # Get today's check-in data if today is in the report range
    checkin_data = {}
    if start_date.date() <= today <= end_date.date():
        checkin_data = get_todays_checkins(employee_ids)
    
    attendance_records = frappe.get_all('Attendance', filters={
        'attendance_date': ['between', [start_date_str, end_date_str]],
        'employee': ['in', employee_ids],
        'docstatus': 1
    }, fields=['employee', 'attendance_date', 'in_time', 'out_time', 'status'])

    attendance_dict = {}
    for record in attendance_records:
        in_time = record['in_time'].strftime('%H:%M') if record['in_time'] else None
        out_time = record['out_time'].strftime('%H:%M') if record['out_time'] else None
        attendance_dict.setdefault(record['employee'], {})[record['attendance_date']] = {
            'in_time': in_time,
            'out_time': out_time,
            'status': record['status']
        }

    serial_number = 1
    for employee in employee_ids:
        row = {
            'serial_number': serial_number,
            'employee_id': employee
        }
        
        get_holiday = frappe.db.get_value("Attendance", {
            "attendance_date": ["between", [start_date, end_date]],
            "employee": employee,
            "status": ["in", ["Present", "Work From Home"]],
            "docstatus": 1
        }, ['holiday_list'], order_by="attendance_date ASC")
        holiday_name = get_holiday or frappe.db.get_value("Employee", employee, "holiday_list")
        
        holiday_list = []
        if holiday_name:
            query = """
                SELECT holiday_date, weekly_off, description
                FROM tabHoliday 
                WHERE parent = %s 
                AND parentfield = 'holidays' 
                AND parenttype = 'Holiday List';
            """
            holiday_list = frappe.db.sql(query, (holiday_name,), as_dict=True)

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            is_today = current_date.date() == today
            
            # Check for live check-in data first for today
            if is_today and employee in checkin_data:
                checkins = checkin_data[employee]
                in_times = [c['time'] for c in checkins if c['type'] == 'IN' and c['time'] is not None]
                out_times = [c['time'] for c in checkins if c['type'] == 'OUT' and c['time'] is not None]
                
                if in_times or out_times:
                    row[f'in_{current_date.day}'] = format_with_color(
                        convert_to_am_pm(in_times[0]) if in_times else '-', 
                        'green'
                    )
                    row[f'out_{current_date.day}'] = format_with_color(
                        convert_to_am_pm(out_times[-1]) if out_times else '-', 
                        'green'
                    )
                    current_date += timedelta(days=1)
                    continue
            
            # Existing attendance processing
            attendance = attendance_dict.get(employee, {}).get(current_date.date(), None)
            draft_request = get_draft_requests(filters, employee)
            
            if attendance and attendance['status'] == 'Present':
                row[f'in_{current_date.day}'] = format_with_color(
                    convert_to_am_pm(attendance['in_time']) if attendance['in_time'] else '-', 
                    'green'
                )
                row[f'out_{current_date.day}'] = format_with_color(
                    convert_to_am_pm(attendance['out_time']) if attendance['out_time'] else '-', 
                    'green'
                )
            elif attendance and attendance['status'] == 'Work From Home':
                row[f'in_{current_date.day}'] = format_with_color('WFH', 'blue')
                row[f'out_{current_date.day}'] = format_with_color('WFH', 'blue')
            elif attendance and attendance['status'] == 'On Leave':
                row[f'in_{current_date.day}'] = format_with_color('L', 'orange')
                row[f'out_{current_date.day}'] = format_with_color('L', 'orange')
            else:
                is_holiday_or_weekly_off = False
                for holiday in holiday_list:
                    if holiday["holiday_date"] == current_date.date():
                        is_holiday_or_weekly_off = True
                        if holiday['weekly_off'] == 1:
                            row[f'in_{current_date.day}'] = format_with_color('W', 'purple')
                            row[f'out_{current_date.day}'] = format_with_color('W', 'purple')
                        elif holiday['weekly_off'] == 0:
                            row[f'in_{current_date.day}'] = format_with_color('H', 'brown')
                            row[f'out_{current_date.day}'] = format_with_color('H', 'brown')
                        break

                if not is_holiday_or_weekly_off:
                    row[f'in_{current_date.day}'] = format_with_color('A', 'red')
                    row[f'out_{current_date.day}'] = format_with_color('A', 'red')

            for lr in draft_request.get("leave_applications", []):
                if lr.start_date <= current_date.day <= lr.to_date:
                    row[f'in_{current_date.day}'] = format_with_color('L.App', 'green')
                    row[f'out_{current_date.day}'] = format_with_color('L.App', 'green')

            for ar in draft_request.get("attendance_requests", []):
                if ar.start_date <= current_date.day <= ar.to_date:
                    row[f'in_{current_date.day}'] = format_with_color('A.App', 'hotpink')
                    row[f'out_{current_date.day}'] = format_with_color('A.App', 'hotpink')

            current_date += timedelta(days=1)
        
        data.append(row)
        serial_number += 1

    return data

def get_draft_requests(filters: Filters, employee: str) -> Dict:
    """Fetches draft leave applications and attendance requests."""
    LeaveApp = frappe.qb.DocType("Leave Application")
    AttendanceRequest = frappe.qb.DocType("Attendance Request")
    Employee = frappe.qb.DocType("Employee")
    status_condition = (Employee.status == "Active") if filters.get("is_active") else (Employee.status != "Active")
    
    leave_apps = (
        frappe.qb.from_(LeaveApp)
        .join(Employee).on(Employee.name == LeaveApp.employee)
        .select(
            LeaveApp.employee,
            Extract("day", LeaveApp.from_date).as_("start_date"),
            Extract("day", LeaveApp.to_date).as_("to_date"),
            Extract("month", LeaveApp.from_date).as_("start_month"),
            Extract("month", LeaveApp.to_date).as_("to_month"),
            LeaveApp.from_date,
        )
        .where(
            (LeaveApp.docstatus == 0)  # Draft status
            & (LeaveApp.status == "Open")
            & (LeaveApp.employee == employee)
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
    ).run(as_dict=True)
    
    att_requests = (
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
            (AttendanceRequest.docstatus == 0)  # Draft status
            & (AttendanceRequest.workflow_state == "Applied")
            & (AttendanceRequest.employee == employee)
            & (Extract("month", AttendanceRequest.from_date) == filters.month)
            & (Extract("year", AttendanceRequest.from_date) == filters.year)
            & (status_condition)
        )
    ).run(as_dict=True)
    
    return {
        "leave_applications": leave_apps,
        "attendance_requests": att_requests,
    }

def convert_to_am_pm(time_str):
    """Convert time from 24-hour format (HH:MM) to 12-hour format with AM/PM."""
    if not time_str:
        return None
        
    try:
        if isinstance(time_str, str):
            # Handle time strings with or without seconds
            if time_str.count(':') == 1:
                time_obj = datetime.strptime(time_str, "%H:%M")
            else:
                time_obj = datetime.strptime(time_str, "%H:%M:%S")
            return time_obj.strftime("%I:%M %p").lstrip('0')
        elif hasattr(time_str, 'strftime'):
            return time_str.strftime("%I:%M %p").lstrip('0')
        return time_str
    except ValueError:
        return time_str  # Return original if conversion fails

def format_with_color(text, color):
    """Wrap text in HTML to display colored text in the report."""
    if text is None:
        return ''
    return f'<span style="color: {color};">{text}</span>'