import frappe
from datetime import datetime, timedelta
from frappe.query_builder.functions import Count, Extract, Sum
from typing import Dict, List, Optional, Tuple
Filters = frappe._dict

def execute(filters=None):
    # Main function to execute the report
    if filters:
        validate_filters(filters)
    
    # Get the columns and data for the report
    columns = get_columns(filters)
    # get the data
    data = get_data(filters)
    # return the columns and data
    return columns, data

def validate_filters(filters):
    """Validate that the date range falls within the selected month."""
    date_range = filters.get('date_range')
    
    if not date_range or len(date_range) != 2:
        frappe.throw("Please select a valid date range.")
    
    # Assign start and end date
    start_date_str, end_date_str = date_range[0], date_range[1]
    
    # Convert start_date and end_date to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Get the selected month and year from filters
    month = int(filters.get('month'))
    year = int(filters.get('year'))
    
    # Check if the start and end dates are in the same month and year
    if  start_date.year != year or end_date.year != year:
        frappe.throw("The date range must be within the selected year.")
    
    # Check that the start date is before or equal to the end date
    if start_date > end_date:
        frappe.throw("The start date cannot be later than the end date.")

def get_columns(filters):
    # Function to generate dynamic columns based on the date range
    columns = []
    
    # Add Serial Number Column
    # columns.append({
    #     "label": "SL #",
    #     "fieldname": "serial_number",
    #     "fieldtype": "Int",
    #     "width": 80,
    #     "align": "center"
    # })

    # Add Employee ID column
    columns.append({
        "label": "Employee ID",
        "fieldname": "employee_id",
        "fieldtype": "Link",
        "options": "Employee",
        "width": 120
    })

    # Get the start and end date from the filters
    date_range = filters.get("date_range")
    if not date_range or len(date_range) != 2:
        return columns  # Return an empty column set if date range is invalid
    
    start_date_str = date_range[0]
    end_date_str = date_range[1]
    
    # Convert the start and end dates to datetime objects
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Generate columns for each day in the date range with subcolumns
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%d-%b-%Y")
        
        # Add grouped columns for In and Out for each date
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
        
        # Move to the next day
        current_date += timedelta(days=1)
    
    return columns

def get_data(filters):
    # Function to fetch and process data for the report
    data = []

    # Fetch employees based on the filters or all employees
    # employee_ids = filters.get('employee') or frappe.get_all('Employee', pluck='name')
    # department_filter = filters.get('department')
    # job_location=filters.get('job_location')
    # reporting_location=filters.get('reporting_location')
    # if department_filter:
    #     employee_ids = frappe.get_all('Employee', filters={'department': department_filter}, pluck='name')
    # employee_ids = filters.get('employee')  # Fetch employee(s) from the filter
    employee_ids = []
    # If no specific employee is selected, fetch all employees based on other filters (department, job location, etc.)
    if not employee_ids or len(employee_ids) == 0:
        conditions = {}
        # only get active employee
        conditions['status'] = 'Active'
        if filters.get('department'):
            conditions['department'] = filters.get('department')
        if filters.get('excel_job_location'):
            conditions['excel_job_location'] = filters.get('excel_job_location')
        if filters.get('excel_reporting_location'):
            conditions['excel_reporting_location'] = filters.get('excel_reporting_location')
        # if employee need in operator
        if filters.get('employee'):
            conditions['name'] = ['in', filters.get('employee')]
        # only get active employee


        employee_ids = frappe.get_all('Employee', filters=conditions, pluck='name')
        frappe.errprint(frappe.as_json(employee_ids))


    # Ensure employee_ids is a list
    if isinstance(employee_ids, str):
        employee_ids = [employee_ids]

    # If no employees are found, return an empty data set
    if not employee_ids:
        return data
    # Get the start and end date from the filters
    start_date_str = filters.get("date_range")[0]
    end_date_str = filters.get("date_range")[1]
    
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    # Fetch Attendance records for the date range and employee list
    attendance_records = frappe.get_all('Attendance', filters={
        'attendance_date': ['between', [start_date_str, end_date_str]],
        'employee': ['in', employee_ids],
        'docstatus': 1  # Only fetch submitted records
    }, fields=['employee', 'attendance_date', 'in_time', 'out_time', 'status'])

    # Create a dictionary for quick lookup by employee and date
    attendance_dict = {}
    for record in attendance_records:
        # Only attempt to format in_time and out_time if they are valid time values
        in_time = record['in_time'].strftime('%H:%M') if record['in_time'] else None
        out_time = record['out_time'].strftime('%H:%M') if record['out_time'] else None

        # Set the status if it is not "Present" and there is no valid in_time or out_time
        attendance_dict.setdefault(record['employee'], {})[record['attendance_date']] = {
            'in_time': in_time,
            'out_time': out_time,
            'status': record['status'],
            'attendance_date': record['attendance_date']
        }

    # Iterate over each employee and populate the data
    serial_number = 1
    for employee in employee_ids:
        row = {
            'serial_number': serial_number,
            'employee_id': employee
        }
        
        # Get holiday list for the employee
        get_holiday = frappe.db.get_value("Attendance", {
            "attendance_date": ["between", [start_date, end_date]],
            "employee": employee,
            "status": ["in", ["Present", "Work From Home"]],
            "docstatus": 1
        }, ['holiday_list'], order_by="attendance_date ASC")
        holiday_name = get_holiday or frappe.db.get_value("Employee", employee, "holiday_list")
        
        # Fetch holiday list details
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

        # Process attendance for each day in the date range
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            attendance = attendance_dict.get(employee, {}).get(current_date.date(), None)
            draft_request=get_draft_requests(filters,employee)
            # Check attendance status and set appropriate values
            
            if attendance and attendance['status'] == 'Present':
                row[f'in_{current_date.day}'] = format_with_color(convert_to_am_pm(attendance['in_time']), 'green') if attendance['in_time'] else '-'
                row[f'out_{current_date.day}'] = format_with_color(convert_to_am_pm(attendance['out_time']), 'green') if attendance['out_time'] else '-'
            elif attendance and attendance['status'] == 'Work From Home':
                row[f'in_{current_date.day}'] = format_with_color('WFH', 'blue')
                row[f'out_{current_date.day}'] = format_with_color('WFH', 'blue')
            elif attendance and attendance['status'] == 'On Leave':
                row[f'in_{current_date.day}'] = format_with_color('L', 'orange')
                row[f'out_{current_date.day}'] = format_with_color('L', 'orange')
            else:
                # Check for holidays and weekly offs
                is_holiday_or_weekly_off = False
                for holiday in holiday_list:
                    if holiday["holiday_date"] == current_date.date():
                        is_holiday_or_weekly_off = True
                        if holiday['weekly_off'] == 1:
                            row[f'in_{current_date.day}'] = format_with_color('W', 'purple')  # Weekly off
                            row[f'out_{current_date.day}'] = format_with_color('W', 'purple')
                        elif holiday['weekly_off'] == 0:
                            row[f'in_{current_date.day}'] = format_with_color('H', 'brown')  # Holiday
                            row[f'out_{current_date.day}'] = format_with_color('H', 'brown')
                        break

                # If not a holiday or weekly off, mark as absent
                if not is_holiday_or_weekly_off:
                    row[f'in_{current_date.day}'] = format_with_color('A', 'red')
                    row[f'out_{current_date.day}'] = format_with_color('A', 'red')
                    # make here draft request
            for lr in draft_request.get("leave_applications", []):
              
                if lr.start_date <= current_date.day <= lr.to_date:
                    # print(lr.start_date,current_date.day,lr.to_date)
                    row[f'in_{current_date.day}'] = format_with_color('L.App', 'green')
                    row[f'out_{current_date.day}'] = format_with_color('L.App', 'green')

            for ar in draft_request.get("attendance_requests", []):
                print(ar)
                if ar.start_date <= current_date.day <= ar.to_date:
                    row[f'in_{current_date.day}'] = format_with_color('A.App', 'hotpink')
                    row[f'out_{current_date.day}'] = format_with_color('A.App', 'hotpink')

            # Move to the next day
            current_date += timedelta(days=1)
        
        data.append(row)
        serial_number += 1

    return data


def get_draft_requests(filters: Filters,employee:str) -> Dict:
    """Fetches draft leave applications and attendance requests."""
    LeaveApp = frappe.qb.DocType("Leave Application")
    AttendanceRequest = frappe.qb.DocType("Attendance Request")
    
    leave_apps = (
        frappe.qb.from_(LeaveApp)
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
            & (LeaveApp.employee == employee)
            & (
                (Extract("month", LeaveApp.from_date) == filters.month) |
                (Extract("month", LeaveApp.to_date) == filters.month)
            )
            & (
                (Extract("year", LeaveApp.from_date) == filters.year) |
                (Extract("year", LeaveApp.to_date) == filters.year)
            )
        )
    ).run(as_dict=True)
    
    att_requests = (
        frappe.qb.from_(AttendanceRequest)
        .select(
            AttendanceRequest.employee,
            Extract("day", AttendanceRequest.from_date).as_("start_date"),
            Extract("day", AttendanceRequest.to_date).as_("to_date"),
            Extract("month", AttendanceRequest.from_date).as_("start_month"),
            Extract("month", AttendanceRequest.to_date).as_("to_month"),
        )
        .where(
            (AttendanceRequest.docstatus == 0)  # Draft status
            & (AttendanceRequest.employee == employee)
            & (Extract("month", AttendanceRequest.from_date) == filters.month)
            & (Extract("year", AttendanceRequest.from_date) == filters.year)
        )
    ).run(as_dict=True)
    print({
        "leave_applications": leave_apps,
        "attendance_requests": att_requests,
    })
    
    return {
        "leave_applications": leave_apps,
        "attendance_requests": att_requests,
    }



def convert_to_am_pm(time_str):
    """Convert time from 24-hour format (HH:MM) to 12-hour format with AM/PM."""
    # Parse the time string into a datetime object
    time_obj = datetime.strptime(time_str, "%H:%M")
    
    # Convert to 12-hour format with AM/PM
    return time_obj.strftime("%I:%M %p").lstrip('0')
def format_with_color(text, color):
    """Wrap text in HTML to display colored text in the report."""
    return f'<span style="color: {color};">{text}</span>'
