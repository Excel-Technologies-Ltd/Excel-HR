from frappe import _
import frappe
from datetime import datetime, timedelta
import calendar
from datetime import time
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    employee_details_message = get_employee_details(filters.get('employee'))
    return columns, data, employee_details_message

def get_columns():
    columns = [
        _("Date") + "::100",
        _("Employee Name") + "::170",
        _("Roster Time") + "::150",
        _("In Time") + "::80",
        _("Out Time") + "::80",
        _("W. Hours") + "::70",
        _("Initial Status") + "::150",
        _("Payroll Status") + "::100",
        _("Remarks") + "::200",
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
    if not attendance_list:
        return
    # frappe.msgprint(f"Attendance Records: {frappe.as_json(attendance_list)}")
    # Get the days in the month
    if month ==current_month and year==current_year:
        end_day=current_date.day 
    else:
        end_day= calendar.monthrange(year, month)[1]
    all_dates= [datetime(year, month, day).date() for day in range(1, end_day + 1)]
    print(all_dates)
    # days_in_month = calendar.monthrange(year, month)[1]

    # # Create a list of all dates in the month
    # all_dates = [datetime(year, month, day).date() for day in range(1, days_in_month + 1)]

    formatted_data = []

    # Retrieve employee name once
    employee_name = frappe.db.get_value("Employee", filters.get('employee'), "employee_name")
    holiday_name = frappe.db.get_value("Employee", filters.get('employee'), "holiday_list")
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
                    SELECT holiday_date, weekly_off 
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

    # Populate the formatted_data list with attendance data and fill in missing dates with None
    for date in all_dates:
        attendance = next((item for item in attendance_list if item['attendance_date'] == date), None)

        if attendance:
            in_time = attendance.get('in_time')
            out_time = attendance.get('out_time')

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
               f"{ attendance.get('working_hours')} h",
                get_status(attendance ,data,date),
                "Present"if attendance.get('status')=="On Leave" else attendance.get('status'),
                None,
                
            ])
        else:
            formatted_data.append([date, employee_name, None if get_holiday_status(data,date) else shift_time_string, None,None, None,get_holiday_status(data,date),"Present" if get_holiday_status(data,date) else None,None])

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
        return
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
    

    