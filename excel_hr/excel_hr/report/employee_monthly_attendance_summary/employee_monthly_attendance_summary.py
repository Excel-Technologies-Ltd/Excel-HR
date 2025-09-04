from frappe import _
import frappe
from datetime import datetime, date, timedelta
import calendar
from frappe.query_builder.functions import Count, Extract, Sum

# def execute(filters=None):
#     columns = get_columns()
#     data = get_data(filters)
#     employee_details_message = get_employee_details(filters.get('employee'))
#     return columns, data, employee_details_message




def get_columns():
    columns = [
        {
            "fieldname": "date",
            "label": _("Date"),
            "fieldtype": "Data",
            "width": 100,
            "align": "left"
        },
        {
            "fieldname": "employee_name",
            "label": _("Employee Name"),
            "fieldtype": "Data",
            "width": 170,
            "align": "left"
        },
        {
            "fieldname": "roster_time",
            "label": _("Roster Time"),
            "fieldtype": "Data",
            "width": 150,
            "align": "left"
        },
        {
            "fieldname": "in_time",
            "label": _("In Time"),
            "fieldtype": "Data",
            "width": 80,
            "align": "left"
        },
        {
            "fieldname": "out_time",
            "label": _("Out Time"),
            "fieldtype": "Data",
            "width": 80,
            "align": "left"
        },
        {
            "fieldname": "worked_hours",
            "label": _("W. Hours"),
            "fieldtype": "Data",
            "width": 70,
            "align": "left"
        },
        {
            "fieldname": "initial_status",
            "label": _("Initial Status"),
            "fieldtype": "Data",
            "width": 150,
            "align": "left"
        },
        {
            "fieldname": "payroll_status",
            "label": _("Payroll Status"),
            "fieldtype": "Data",
            "width": 100,
            "align": "left"
        },
        {
            "fieldname": "remarks",
            "label": _("Remarks"),
            "fieldtype": "Small Text",
            "width": 220,
            "align": "left"
        },
    ]
    return columns


def get_data(filters):
    if not filters.get('employee'):
        return []

    employee_id = filters.get('employee')
    month = int(filters.get('month'))
    year = int(filters.get('year'))

    attendance_list = get_attendance_by_employee_and_month(employee_id, month, year)

    end_day = calendar.monthrange(year, month)[1]
    all_dates = [datetime(year, month, day).date() for day in range(1, end_day + 1)]

    employee_name = frappe.db.get_value("Employee", employee_id, "employee_name")

    start_date = f"{year}-{month}-01"
    end_date_str = f"{year}-{month}-15"
    get_holiday = frappe.db.get_value("Attendance", {
        "attendance_date": ["between", [start_date, end_date_str]],
        "employee": employee_id,
        "status": ["in", ["Present", "Work From Home"]],
        "docstatus": 1
    }, ['holiday_list'], order_by="attendance_date ASC")
    holiday_name = get_holiday or frappe.db.get_value("Employee", employee_id, "holiday_list")
    holidays_data = []
    if holiday_name:
        query = """
            SELECT holiday_date, weekly_off, description
            FROM tabHoliday
            WHERE parent = %s
              AND parentfield = 'holidays'
              AND parenttype = 'Holiday List'
        """
        holidays_data = frappe.db.sql(query, (holiday_name,), as_dict=True)

    shift_name = frappe.db.get_value("Employee", employee_id, "default_shift")
    shift_time_string = None
    if shift_name:
        shift_time = frappe.db.get_value("Shift Type", shift_name, ['start_time', 'end_time'])
        if shift_time and len(shift_time) == 2:
            shift_in_time = convert_single_time_format(shift_time[0])
            shift_out_time = convert_single_time_format(shift_time[1])
            shift_time_string = f"{shift_in_time} to {shift_out_time}"

    draft_data = get_draft_requests(filters)

    today_date = datetime.today().date()
    if today_date.year == year and today_date.month == month:
        first_checkin, last_checkout = get_today_checkin_checkout(employee_id)
        today_attendance = next(
            (item for item in attendance_list if item['attendance_date'] == today_date), 
            None
        )
        if first_checkin and last_checkout:
            if today_attendance:
                today_attendance.update({
                    'in_time': first_checkin,
                    'out_time': last_checkout,
                    'status': 'Present',
                    'working_hours': (last_checkout - first_checkin).seconds / 3600.0,
                    'late_entry': 0,
                    'early_exit': 0
                })
            else:
                attendance_list.append({
                    'attendance_date': today_date,
                    'employee': employee_id,
                    'employee_name': employee_name,
                    'in_time': first_checkin,
                    'out_time': '',
                    'status': 'Present',
                    'working_hours': '', #(last_checkout - first_checkin).seconds / 3600.0,
                    'leave_application': None,
                    'attendance_request': None,
                    'late_entry': 0,
                    'early_exit': 0,
                    'shift': shift_name or None
                })

    formatted_data = []

    for current_date in all_dates:
        attendance = next((item for item in attendance_list if item['attendance_date'] == current_date), None)
        attendance_request_remarks = ""
        leave_application_remarks = ""
        is_draft_leave = any(lr["start_date"] <= current_date <= lr["to_date"] for lr in draft_data.get("leave_applications", []))
        is_draft_attendance = any(ar["start_date"] <= current_date <= ar["to_date"] for ar in draft_data.get("attendance_requests", []))

        if isinstance(current_date, (datetime, date)):
            date_str = current_date.strftime('%Y-%m-%d')
        else:
            date_str = str(current_date)

        if attendance:
            in_time = attendance.get('in_time')
            out_time = attendance.get('out_time')
            attendance_request = attendance.get('attendance_request')
            leave_application = attendance.get('leave_application')

            if attendance_request:
                attendance_request_remarks = frappe.db.get_value('Attendance Request', attendance_request, ['explanation']) or ""

            if leave_application:
                leave_application_remarks = frappe.db.get_value('Leave Application', leave_application, ['description']) or ""

            if isinstance(in_time, (datetime, date)):
                in_time_str = in_time.strftime('%I:%M %p')
            else:
                in_time_str = in_time

            if isinstance(out_time, (datetime, date)):
                out_time_str = out_time.strftime('%I:%M %p')
            else:
                out_time_str = out_time

            worked_hours = "" if attendance.get('status') in ["Work From Home", "On Leave"] else f"{attendance.get('working_hours', ''):.1f} h" if attendance.get('working_hours') else ""

            if current_date == datetime.today().date() and attendance.get('in_time'):
                payroll_status = "<span style='color:#1d88e5; text-style=bold'>Pending</span>"
            else:
                payroll_status = ("Present" if attendance.get('status') in ["On Leave", "Work From Home", "Weekend"] 
                                else attendance.get('status'))
            formatted_data.append([
            current_date.strftime('%Y-%m-%d') if isinstance(current_date, date) else current_date,
            attendance.get('employee_name'),
            shift_time_string,
            in_time_str,
            out_time_str,
            worked_hours,
            get_status(attendance, holidays_data, current_date),
            payroll_status,
            attendance_request_remarks or leave_application_remarks,
            ])
        else:
            status = 'Absent'
            draft_remarks = None
            if is_draft_leave:
                draft_remarks = 'Leave Application (Pending)'
            elif is_draft_attendance:
                draft_remarks = 'Attendance Request (Pending)'

            formatted_data.append([
                date_str,
                employee_name,
                shift_time_string,
                None,
                None,
                None,
                get_holiday_status(holidays_data, current_date),
                get_holiday_payroll_status(holidays_data, current_date) if get_holiday_payroll_status(holidays_data, current_date) else "<span style='color:red;'>Absent</span>" if status == 'Absent' else status,
                get_holiday_status_remarks(holidays_data, current_date, draft_remarks)
            ])

    return formatted_data


def get_attendance_by_employee_and_month(employee_id, month, year):
    current_year = year
    query = f"""
        SELECT working_hours, leave_application, early_exit,
          shift, late_entry, attendance_request, status, 
          employee_name, employee, attendance_date, in_time, out_time, 
          (SELECT employee_name 
            FROM `tabEmployee` 
            WHERE name = `tabAttendance`.employee ) AS employee_name
        FROM `tabAttendance`
        WHERE `employee` = '{employee_id}'
        AND YEAR(`attendance_date`) = {current_year}
          AND MONTH(`attendance_date`) = {month}
          AND `docstatus`={1}
    """
    attendance_records = frappe.db.sql(query, as_dict=True)
    return attendance_records


def get_employee_details(employee_id):
    if not employee_id:
        return
    employee = frappe.get_doc("Employee", employee_id)
    shift_name = frappe.db.get_value("Employee", employee_id, "default_shift")
    if shift_name:
        shift_time = frappe.db.get_value("Shift Type", shift_name, ['start_time', 'end_time'])
        shift_in_time = convert_single_time_format(shift_time[0])
        shift_out_time = convert_single_time_format(shift_time[1])
        shift_time_string = f"{shift_in_time} to {shift_out_time}"
    else:
        shift_time_string = ""

    employee_details = {
        "Employee Name": employee.get('employee_name', ''),
        "Employee ID": employee.get('name', ''),
        "Designation": employee.get('designation', ''),
        "Department": employee.get('department', ''),
        # "Shift Time": shift_time_string,
        "Job Location": employee.get('custom_job_location', ''),
        "Joining Date": employee.get('date_of_joining', ''),
        "Contact Number": employee.get('excel_official_mobile_no', ''),
        "Email": employee.get('company_email', ''),
        "Manager Name": frappe.db.get_value("User", employee.get('leave_approver'), 'full_name')
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
    message += "</div>"

    return message


def convert_single_time_format(time_str):
    time_obj = datetime.strptime(str(time_str), "%H:%M:%S")
    formatted_time = time_obj.strftime("%I:%M %p").lstrip("0").replace(" 0", " ")
    return formatted_time


def get_status(d, date_list, current_date):
    status = d.get('status', 'Absent')

    if date_list:
        if current_date in date_list:
            status = "WE"

    if status == 'Present' and d.get('late_entry', 0) == 0 and d.get('early_exit', 0) == 0:
        if d.get('attendance_request'):
            data = frappe.db.get_value('Attendance Request', d.get('attendance_request'), ['reason', 'excel_criteria_of_reason'])
            if data:
                reason = data[0]
                criteria = data[1]
                if reason == 'On Duty' and criteria == 'Foreign Tour':
                    status = 'Foreign Tour'
                elif reason == 'On Duty' and criteria == 'Local Tour':
                    status = 'Local Tour'
                elif reason == 'On Duty' and criteria == 'Off Day Duty':
                    status = "Off Day Duty"
                elif reason == 'On Duty':
                    status = "Outside Duty"
        else:
            status = "Present"
    elif status == 'Present' and d.get('late_entry', 0) == 1 and d.get('early_exit', 0) == 0:
        status = "Late IN"
    elif status == 'Present' and d.get('late_entry', 0) == 0 and d.get('early_exit', 0) == 1:
        status = "Early OUT"
    elif status == 'Present' and d.get('late_entry', 0) == 1 and d.get('early_exit', 0) == 1:
        status = "Late IN & Early OUT"
    elif status == "On Leave":
        data = frappe.db.get_value('Leave Application', d.get('leave_application'), ['leave_type', 'excel_leave_category'])
        if data:
            leave_type = data[0]
            leave_category = data[1]
            if leave_type == "Special Leave" and leave_category == "Casual":
                status = 'Special Leave (Casual)'
            elif leave_type == "Special Leave" and leave_category == "Medical":
                status = "Special Leave (Medical)"
            elif leave_type == "Monthly Paid Leave":
                status = "Monthly Paid Leave"
            elif leave_type == "Annual Leave" and leave_category == "Casual":
                status = "Annual Leave (Casual)"
            elif leave_type == "Annual Leave" and leave_category == "Medical":
                status = "Annual Leave (Medical)"
            elif leave_type == "Compensatory Leave":
                status = "Compensatory Leave"
            elif leave_type == "Leave Without Pay":
                status = "Leave Without Pay"
            elif leave_type == "Maternity Leave":
                status = "Maternity Leave"
    else:
        status = status

    return status


def get_holiday_status(date_list, current_date):
    holiday_info = {holiday["holiday_date"]: holiday["weekly_off"] for holiday in date_list}
    if current_date in holiday_info:
        if holiday_info[current_date] == 1:
            return "Weekend"
        else:
            return "Holiday"


def get_holiday_payroll_status(date_list, current_date):
    holiday_info = {str(holiday["holiday_date"]): holiday["weekly_off"] for holiday in date_list}
    if str(current_date) in holiday_info:
        return "Present"


def get_holiday_status_remarks(date_list, current_date, draft_remarks=None):
    if draft_remarks:
        return draft_remarks
    holiday_info = {
        str(holiday["holiday_date"]): {
            "weekly_off": holiday["weekly_off"],
            "description": holiday.get("description", "")
        }
        for holiday in date_list
    }
    if str(current_date) in holiday_info:
        holiday_details = holiday_info[str(current_date)]
        weekly_off = holiday_details["weekly_off"]
        description = holiday_details["description"]

        if weekly_off == 0:
            return description if description else ""
        else:
            return ""


def get_draft_requests(filters):
    if not filters.get("employee"):
        return {"leave_applications": [], "attendance_requests": []}
    LeaveApp = frappe.qb.DocType("Leave Application")
    leave_apps = (
        frappe.qb.from_(LeaveApp)
        .select(
            LeaveApp.employee,
            LeaveApp.from_date.as_("start_date"),
            LeaveApp.to_date.as_("to_date")
        )
        .where(
            (LeaveApp.docstatus == 0) &
            (LeaveApp.employee == filters.get("employee")) &
            (LeaveApp.status == "Open") &
            (
                (Extract("month", LeaveApp.from_date) == filters.get("month")) |
                (Extract("month", LeaveApp.to_date) == filters.get("month"))
            ) &
            (
                (Extract("year", LeaveApp.from_date) == filters.get("year")) |
                (Extract("year", LeaveApp.to_date) == filters.get("year"))
            )
        )
    ).run(as_dict=True)

    AttendanceRequest = frappe.qb.DocType("Attendance Request")
    att_requests = (
        frappe.qb.from_(AttendanceRequest)
        .select(
            AttendanceRequest.employee,
            AttendanceRequest.from_date.as_("start_date"),
            AttendanceRequest.to_date.as_("to_date")
        )
        .where(
            (AttendanceRequest.docstatus == 0) &
            (AttendanceRequest.workflow_state == "Applied") &
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
    ).run(as_dict=True)

    return {
        "leave_applications": leave_apps,
        "attendance_requests": att_requests
    }


def get_today_checkin_checkout(employee_id):
    today = datetime.today().date()
    print("Today's date:", today)

    checkins = frappe.get_all("Employee Checkin",
        filters={
            "employee": employee_id,
            "date": ["=", today],
        },
        fields=["name", "time", "log_type"],
        order_by="time ASC"
    )
    print("Check-ins for today:", checkins)
    if not checkins:
        return None, None

    first_in = checkins[0]['time']
    last_out = checkins[-1]['time']

    return first_in, last_out
