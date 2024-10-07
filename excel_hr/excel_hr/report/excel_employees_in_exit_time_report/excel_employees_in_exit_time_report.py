import frappe
from datetime import datetime, timedelta

def execute(filters=None):
    # Validate the filters
    if filters:
        validate_filters(filters)
    
    # Generate columns dynamically based on date range
    columns = get_columns(filters)
    
    # Fetch data from the Attendance Doctype
    data = get_data(filters)
    
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
    columns = []
    
    # Add Serial Number Column
    columns.append({
        "label": "SL #",
        "fieldname": "serial_number",
        "fieldtype": "Int",
        "width": 80,
        "align": "center"
    })

    # Add Employee ID column
    columns.append({
        "label": "Employee ID",
        "fieldname": "employee_id",
        "fieldtype": "Data",
        "width": 150
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
            "label": f"{date_str} (In Time)",
            "fieldname": f"in_{current_date.day}",
            "fieldtype": "Data",
            "width": 200,
            "align": "center"
        })
        columns.append({
            "label": f"{date_str} (Out Time)",
            "fieldname": f"out_{current_date.day}",
            "fieldtype": "Data",
            "width": 200,
            "align": "center"
        })
        
        # Move to the next day
        current_date += timedelta(days=1)
    
    return columns

def get_data(filters):
    data = []

    # Fetch employees based on the filters or all employees
    employee_ids = filters.get('employee') or frappe.get_all('Employee', pluck='name')

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
    }, fields=['employee', 'attendance_date', 'in_time', 'out_time','status'])

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
            'status':record['status'],
            'attendance_date':record['attendance_date']
        }



    # Iterate over each employee and populate the data
    serial_number = 1
    for employee in employee_ids:
        row = {
            'serial_number': serial_number,
            'employee_id': employee
        }

        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            attendance = attendance_dict.get(employee, {}).get(current_date.date(), None)
            print(attendance)

            # Check if attendance exists and handle None cases
            if attendance and attendance['status']== 'Present':
                row[f'in_{current_date.day}'] = convert_to_am_pm(attendance['in_time']) if attendance['in_time'] else '-'
                row[f'out_{current_date.day}'] = convert_to_am_pm(attendance['out_time']) if attendance['out_time'] else '-'
            elif attendance and attendance['status'] == 'Work From Home':
                row[f'in_{current_date.day}']='WFH'
                row[f'out_{current_date.day}']='WFH'
            elif attendance and  attendance['status'] == 'On Leave':
                row[f'in_{current_date.day}']='L'
                row[f'out_{current_date.day}']='L'               
            else:
                row[f'in_{current_date.day}'] = 'A'
                row[f'out_{current_date.day}'] = 'A'

            # Move to the next day
            current_date += timedelta(days=1)
        
        data.append(row)
        serial_number += 1

    return data


def convert_to_am_pm(time_str):
    """
    Convert time from 24-hour format (HH:MM) to 12-hour format with AM/PM.

    :param time_str: Time in 24-hour format as a string (e.g., "15:32")
    :return: Time in 12-hour format with AM/PM (e.g., "3:32 PM")
    """
    # Parse the time string into a datetime object
    time_obj = datetime.strptime(time_str, "%H:%M")
    
    # Convert to 12-hour format with AM/PM
    return time_obj.strftime("%I:%M %p").lstrip('0')