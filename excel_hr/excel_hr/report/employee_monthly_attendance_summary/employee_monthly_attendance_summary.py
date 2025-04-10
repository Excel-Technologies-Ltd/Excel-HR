from frappe import _
import frappe
from datetime import datetime, timedelta
import calendar
from datetime import time
from frappe.query_builder.functions import Count, Extract, Sum
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    employee_details_message = get_employee_details(filters.get('employee'))
    return columns, data, employee_details_message

def get_columns():
    columns = [
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 100,
            "align": "left"  # Align left
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 170,
            "align": "left"  # Align left
        },
        {
            "fieldname": "roster_time",
            "label": _("Roster Time"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 150,
            "align": "left"  # Align left
        },
        {
            "fieldname": "in_time",
            "label": _("In Time"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 80,
            "align": "left"  # Align left
        },
        {
            "fieldname": "out_time",
            "label": _("Out Time"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 80,
            "align": "left"  # Align left
        },
        {
            "fieldname": "worked_hours",
            "label": _("W. Hours"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 70,
            "align": "left"  # Align left
        },
        {
            "fieldname": "initial_status",
            "label": _("Initial Status"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 150,
            "align": "left"  # Align left
        },
        {
            "fieldname": "payroll_status",
            "label": _("Payroll Status"),
            "fieldtype": "Data",  # Adjust based on your actual data type
            "width": 100,
            "align": "left"  # Align left
        },
        {
            "fieldname": "remarks",
            "label": _("Remarks"),
            "fieldtype": "Small Text",  # Adjust based on your actual data type
            "width": 220,
            "align": "left"  # Align left
        },
    ]
    return columns


def get_data(filters):
    if not filters.get('employee'):
        return []

    # Convert month to integer
    month = int(filters.get('month'))
    year = int(filters.get('year'))
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month
    attendance_list = get_attendance_by_employee_and_month(filters.get('employee'), month,year)
    # if not attendance_list:
    #     return
    # frappe.msgprint(f"Attendance Records: {frappe.as_json(attendance_list)}")
    # Get the days in the month
    # if month ==current_month and year==current_year:
    #     end_day=current_date.day 
    # else:
    end_day= calendar.monthrange(year, month)[1]
    all_dates= [datetime(year, month, day).date() for day in range(1, end_day + 1)]

    # days_in_month = calendar.monthrange(year, month)[1]

    # # Create a list of all dates in the month
    # all_dates = [datetime(year, month, day).date() for day in range(1, days_in_month + 1)]

    formatted_data = []
    start_date= f"{filters.year}-{filters.month}-01"
    end_date= f"{filters.year}-{filters.month}-15"
    get_holiday= frappe.db.get_value("Attendance", {
			"attendance_date":["between",[start_date, end_date]],
			"employee":filters.get('employee'),
           "status":["in",["Present","Work From Home"]],
            "docstatus":1
		}, ['holiday_list'],order_by="attendance_date ASC")
    # Retrieve employee name once
    employee_name = frappe.db.get_value("Employee", filters.get('employee'), "employee_name")
    holiday_name = get_holiday or frappe.db.get_value("Employee", filters.get('employee'), "holiday_list")
    if holiday_name:
        # data = frappe.db.get_list(
		# 	'Holiday',
		# 	filters={
		# 		"parent": holiday_name,
		# 		"parentfield": "holidays",
		# 		"parenttype": "Holiday List"
		# 	},
		# 	fields=['holiday_date','weekly_off']
		# )
        query = """
                    SELECT holiday_date, weekly_off ,description
                    FROM tabHoliday 
                    WHERE parent = %s 
                      AND parentfield = 'holidays' 
                      AND parenttype = 'Holiday List';
                """
        data=frappe.db.sql(query,(holiday_name,),as_dict=True)    
    



    shift_name = frappe.db.get_value("Employee", filters.get('employee'), "default_shift")
    if shift_name:
        shift_time = frappe.db.get_value("Shift Type", shift_name, ['start_time', 'end_time'])
        shift_in_time=convert_single_time_format(shift_time[0])
        shift_out_time=convert_single_time_format(shift_time[1])
        shift_time_string=f"{shift_in_time} to {shift_out_time}"
        
        # shift_type_string=convert_time_format(shift_time)
    draft_data=get_draft_requests(filters)
    # Populate the formatted_data list with attendance data and fill in missing dates with None
    for date in all_dates:
        attendance = next((item for item in attendance_list if item['attendance_date'] == date), None)
        attendance_request_remarks=""
        leave_application_remarks=""
        is_draft_leave = any(lr["start_date"] <= date <= lr["to_date"] for lr in draft_data["leave_applications"])
        is_draft_attendance = any(ar["start_date"] <= date <= ar["to_date"] for ar in draft_data["attendance_requests"])
        if attendance:
            in_time = attendance.get('in_time')
            out_time = attendance.get('out_time')
            attendance_request=attendance.get('attendance_request')
            leave_application=attendance.get('leave_application')
            if attendance_request:
                attendance_request_remarks= frappe.db.get_value('Attendance Request' ,attendance_request ,['explanation']) if attendance_request else ""
                
            if leave_application:
                leave_application_remarks= frappe.db.get_value('Leave Application' ,leave_application ,['description']) if leave_application else ""
               
            if in_time and out_time:
                in_time_str = in_time.strftime('%I:%M %p')
                out_time_str = out_time.strftime('%I:%M %p')
                roster_time = f"{in_time_str} to {out_time_str}"
            else:
                in_time_str = in_time.strftime('%I:%M %p') if in_time else None
                out_time_str = out_time.strftime('%I:%M %p') if out_time else None

            formatted_data.append([
                attendance.get('attendance_date'),
                attendance.get('employee_name'),
                shift_time_string,
                in_time_str,
                out_time_str,
               "" if attendance.get('status') in ["Work From Home", "On Leave"] else f"{attendance.get('working_hours')} h",
                get_status(attendance ,data,date) ,
                "Present"if attendance.get('status') in ["On Leave","Work From Home","Weekend"] else attendance.get('status'),
                attendance_request_remarks or leave_application_remarks,
                
            ])
        else:
            status= 'Absent'
            draft_remarks=None
            if is_draft_leave:
                
                draft_remarks= 'Leave Application (Pending)'
            elif is_draft_attendance:
             
                draft_remarks= 'Attendance Request (Pending)'      
            
            formatted_data.append([date, employee_name, None, None,None, None,get_holiday_status(data,date) , get_holiday_payroll_status(data,date) if get_holiday_payroll_status(data,date) else "<span style='color:red;'>Absent</span>" if status == 'Absent' else status ,get_holiday_status_remarks(data,date,draft_remarks)])

    return formatted_data


def get_attendance_by_employee_and_month(employee_id, month, year):
    # Get the current year
    current_year = year
    # frappe.msgprint(frappe.as_json({
    #     "employee_id": employee_id,
    #     "month": month,
    #     "current_year": current_year
    # }))
    
    query = f"""
        SELECT working_hours, leave_application, early_exit, shift, late_entry, attendance_request, status, employee_name, employee, attendance_date, in_time, out_time, (SELECT employee_name FROM `tabEmployee` WHERE name = `tabAttendance`.employee) AS employee_name
        FROM `tabAttendance`
        WHERE `employee` = '{employee_id}'
        AND YEAR(`attendance_date`) = {current_year}
          AND MONTH(`attendance_date`) = {month}
          AND `docstatus`={1}
          
    """
    # Execute the query without parameter substitution
    attendance_records = frappe.db.sql(query, as_dict=True)
    print({"reports":attendance_records})
    
    

    return attendance_records


def get_employee_details(employee_id):
    if not employee_id:
        return
    # Retrieve employee details from the database
    employee = frappe.get_doc("Employee", employee_id)
    shift_name = frappe.db.get_value("Employee", employee_id, "default_shift")
    if shift_name:
        shift_time = frappe.db.get_value("Shift Type", shift_name, ['start_time', 'end_time'])
        shift_in_time=convert_single_time_format(shift_time[0])
        shift_out_time=convert_single_time_format(shift_time[1])
        shift_time_string=f"{shift_in_time} to {shift_out_time}"    
    
    employee_details = {
        "Employee Name": employee.get('employee_name', ''),
        "Employee ID": employee.get('name', ''),
        "Designation": employee.get('designation', ''),
        "Department": employee.get('department', ''),
        # "Shift Time": shift_time_string,
        "Job Location":employee.get('excel_job_location', ''),
        "Joining Date": employee.get('date_of_joining', ''),
        "Contact Number": employee.get('excel_official_mobile_no', ''),
        "Email": employee.get('company_email', ''),
        "Manager Name": frappe.db.get_value("User",employee.get('leave_approver'),'full_name')
    }

    message = "<div style='font-family: Arial, sans-serif;'>"
    message += "<h2 style='color: #318AD8; text-align: center;'>Employee Details</h2>"
    message += "<table style='border-collapse: collapse; width: 60%; margin: 0 auto;'>"

    for key, value in employee_details.items():
        message += f"""
            <tr>
                <td style='padding: 2px; border: 1px solid #ddd;'><strong>{key}</strong></td>
                <td style='padding: 2px; border: 1px solid #ddd;'>{value}</td>
            </tr>
        """

    message += "</table>"
    # message += "<p style='color: red; font-size: 12px;'><strong>N.B:</strong> Please ensure all details are correct.</p>"
    message += "</div>"

    return message


def convert_time_format(times):
    # Convert the time strings to datetime objects and format them
    formatted_times = [datetime.strptime(time, "%H:%M:%S").strftime("%I:%M %p").lstrip("0").replace(" 0", " ") for time in times]

    # Join the formatted times into a single string
    return f"{formatted_times[0].lower()} to {formatted_times[1].lower()}"



def convert_single_time_format(time_str):
    # Convert the time string to a datetime object
    time_obj = datetime.strptime(str(time_str), "%H:%M:%S")

    # Format the datetime object into a 12-hour time string with an "AM" or "PM" suffix
    formatted_time = time_obj.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")

    return formatted_time

def get_status(d,date_list,date):
    if not d.status:
        status = 'Absent'
    status = d.status
    status = d.get('status')

    if date_list:
        if date in date_list:
            status = "WE"
    # if d.status == "On Leave":
    #     leave_map.setdefault(d.employee, []).append(d.day_of_month)
    #     continue
    # Check multiple conditions and set "GSL" accordingly

    if d.status == 'Present' and d.late_entry == 0 and d.early_exit==0 :
        if d.attendance_request:
           data= frappe.db.get_value('Attendance Request', d.attendance_request, ['reason','excel_criteria_of_reason'])
           if data:
              reason=data[0]
              criteria=data[1] 
           if reason== 'On Duty' and criteria=='Foreign Tour':
               status='Foreign Tour'
           elif reason== 'On Duty' and criteria=='Local Tour':
               status='Local Tour'
           elif reason== 'On Duty' and criteria=='Off Day Duty':
                status= "Off Day Duty"                                                
           elif reason== 'On Duty':
               status="Outside Duty"                                                                      
        else :
            status="Present"                                                   
    elif d.status == 'Present' and d.late_entry == 1 and d.early_exit==0  : 
        status="Late IN"
    elif d.status == 'Present' and d.late_entry == 0  and d.early_exit==1: 
        status="Early OUT" 
    elif d.status == 'Present' and d.late_entry == 1  and d.early_exit==1: 
        status="Late IN & Early OUT"                                                                     	
    elif d.status == "On Leave":
        data= frappe.db.get_value('Leave Application', d.leave_application, ['leave_type','excel_leave_category'])
        print(data)
        leave_type=data[0]
        leave_category=data[1]
        if leave_type =="Special Leave" and leave_category=="Casual":
            status='Special Leave (Casual)'
        elif leave_type =="Special Leave" and leave_category=="Medical":
            status="Special Leave (Medical)"
        # elif leave_type =="Special Leave":
        #     status="Special Leave" 
        elif leave_type =="Monthly Paid Leave":
            status="Monthly Paid Leave"
        elif leave_type =="Annual Leave" and leave_category=="Casual":
            status="Annual Leave (Casual)"
        elif leave_type =="Annual Leave" and leave_category=="Medical":
            status="Annual Leave (Medical)"
        # elif leave_type =="Annual Leave":
        #     status="Annual Leave"
        elif leave_type =="Compensatory Leave":
            status="Compensatory Leave"  
        elif leave_type =="Leave Without Pay":
            status="Leave Without Pay"
        elif leave_type =="Maternity Leave":
            status="Maternity Leave"                                                                                                
    else:
        status = d.status
        
    return status    


def get_holiday_status(date_list, date):
    # Convert list of dictionaries to a list of holiday dates and their properties
    holiday_info = {holiday["holiday_date"]: holiday["weekly_off"] for holiday in date_list}
    
    # Check if the given date is in the holiday dates list
    if date in holiday_info:
        if holiday_info[date] == 1:
            return "Weekend"
        else:
            return "Holiday"
def get_holiday_payroll_status(date_list, date):
    # Convert list of dictionaries to a list of holiday dates and their properties
    holiday_info = {str(holiday["holiday_date"]): holiday["weekly_off"] for holiday in date_list}

    
    # Check if the given date is in the holiday dates list
    if str(date) in holiday_info:
        if holiday_info[str(date)] == 1:
            return "Present"
        else:
            return "Present"


        
def get_holiday_status_remarks(date_list, date,draft_remarks=None):
    if draft_remarks:
        return draft_remarks
    # Convert list of dictionaries to a list of holiday dates and their properties (weekly_off and description)
    holiday_info = {
        str(holiday["holiday_date"]): {
            "weekly_off": holiday["weekly_off"],
            "description": holiday.get("description", "")  # Add description field, with a default empty string
        } 
        for holiday in date_list
    }
    
    # Check if the given date is in the holiday dates list
    if str(date) in holiday_info:
        holiday_details = holiday_info[str(date)]
        weekly_off = holiday_details["weekly_off"]
        description = holiday_details["description"]

        # If it's a holiday (not a weekend), return the description
        if weekly_off == 0:  # Assuming weekly_off == 0 means it's a holiday
            return description if description else ""  # If no description, just return "Holiday"
        else:
            return ""  # If it's a weekend, return "Weekend"
    
def get_draft_requests(filters):
    """
    Fetch draft Leave Applications and Attendance Requests for the selected employee and date range.
    Returns:
    {
        "leave_applications": [...],
        "attendance_requests": [...]
    }
    """
    if not filters.get("employee"):
        return
    
    # Query draft Leave Applications
    LeaveApp = frappe.qb.DocType("Leave Application")
    leave_apps = (
        frappe.qb.from_(LeaveApp)
        .select(
            LeaveApp.employee,
            LeaveApp.from_date.as_("start_date"),
            LeaveApp.to_date.as_("to_date")
        )
        .where(
            (LeaveApp.docstatus == 0) &  # Draft status
           
            (LeaveApp.employee == filters.get("employee")) &
            
            (
                (Extract("month", LeaveApp.from_date) == filters.get("month")) |
                (Extract("month", LeaveApp.to_date) == filters.get("month"))
            ) & 
            (
                (Extract("year", LeaveApp.from_date) == filters.get("year")) |
                (Extract("year", LeaveApp.to_date) == filters.get("year"))
            )
        )
    )



    leave_apps = leave_apps.run(as_dict=True)

    # Query draft Attendance Requests
    AttendanceRequest = frappe.qb.DocType("Attendance Request")
    att_requests = (
        frappe.qb.from_(AttendanceRequest)
        .select(
            AttendanceRequest.employee,
            AttendanceRequest.from_date.as_("start_date"),
            AttendanceRequest.to_date.as_("to_date")
        )
        .where(
            (AttendanceRequest.docstatus == 0) &  # Draft status
            (AttendanceRequest.employee == filters.get("employee")) &
            (
                (Extract("month", AttendanceRequest.from_date) == filters.get("month")) |
                (Extract("month", AttendanceRequest.to_date) == filters.get("month"))
            ) & 
            (
                (Extract("year", AttendanceRequest.from_date) == filters.get("year")) |
                (Extract("year", AttendanceRequest.to_date) == filters.get("year"))
            )
        )
    )

    att_requests = att_requests.run(as_dict=True)

    return {
        "leave_applications": leave_apps,
        "attendance_requests": att_requests
    }



    