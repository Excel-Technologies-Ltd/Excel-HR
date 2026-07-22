import frappe
from datetime import datetime, timedelta
from frappe.query_builder.functions import Extract
from frappe.utils import getdate
from typing import Dict, List, Optional, Tuple
from excel_hr.excel_hr.report.attendance_checkin_utils import get_local_checkin_tags, local_tag
Filters = frappe._dict

def execute(filters=None):
    filters = frappe._dict(filters or {})
    if filters.get('employee') == []:
        filters.pop('employee')
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
    columns.append({
        "label": "Employee Name",
        "fieldname": "employee_name",
        "fieldtype": "Data",
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
        fields=['employee','employee_name', 'time', 'log_type'],
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


def get_active_or_recently_relieved_condition(Employee, filters: Filters, start_date_str: str, end_date_str: str):
    """Employees to include when the "Is Active Employees" filter is on:
    currently Active employees, plus anyone whose Relieving Date falls
    within the selected date range, so their attendance up to their last
    working day still shows instead of disappearing from the Active view."""
    if not filters.get('is_active'):
        return Employee.status != 'Active'

    return (Employee.status == 'Active') | (
        (Employee.relieving_date >= start_date_str) & (Employee.relieving_date <= end_date_str)
    )


def get_employee_details(filters: Filters) -> Dict:
    """Returns {employee: employee_detail_dict} for employees matching the
    report's Employee filters (department/location/employee list/active-or-
    recently-relieved)."""
    Employee = frappe.qb.DocType('Employee')
    date_range = filters.get('date_range')
    start_date_str, end_date_str = date_range[0], date_range[1]

    query = (
        frappe.qb.from_(Employee)
        .select(
            Employee.name,
            Employee.employee_name,
            Employee.status,
            Employee.relieving_date,
            Employee.holiday_list,
            Employee.date_of_joining,
        )
        .where(get_active_or_recently_relieved_condition(Employee, filters, start_date_str, end_date_str))
    )

    if filters.get('department'):
        query = query.where(Employee.department == filters.department)
    if filters.get('custom_job_location'):
        query = query.where(Employee.custom_job_location == filters.custom_job_location)
    if filters.get('custom_reporting_location'):
        query = query.where(Employee.custom_reporting_location == filters.custom_reporting_location)
    if filters.get('employee'):
        employees = filters.employee if isinstance(filters.employee, list) else [filters.employee]
        query = query.where(Employee.name.isin(employees))

    rows = query.run(as_dict=True)
    return {row.name: row for row in rows}


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


def get_holiday_anchors(filters: Filters, employee_ids: List[str]) -> Dict[str, List[Tuple]]:
    """Returns {employee: [(date, holiday_list), ...]} sorted ascending by
    date, drawn from the employee's actual Attendance records for the
    selected month -- used to resolve which Holiday List was in effect
    around a gap in attendance."""
    if not employee_ids:
        return {}

    Attendance = frappe.qb.DocType('Attendance')
    rows = (
        frappe.qb.from_(Attendance)
        .select(Attendance.employee, Attendance.attendance_date, Attendance.holiday_list)
        .where(
            (Attendance.docstatus == 1)
            & (Attendance.employee.isin(employee_ids))
            & (Extract('month', Attendance.attendance_date) == filters.month)
            & (Extract('year', Attendance.attendance_date) == filters.year)
            & (Attendance.holiday_list.isnotnull())
        )
    ).run(as_dict=True)

    anchors = {}
    for r in rows:
        if not r.holiday_list:
            continue
        anchors.setdefault(r.employee, []).append((getdate(r.attendance_date), r.holiday_list))
    for employee in anchors:
        anchors[employee].sort(key=lambda entry: entry[0])
    return anchors


def get_holiday_map(start_date, end_date) -> Dict[str, Dict]:
    """Returns {holiday_list_name: {date: True}} for every Holiday List's
    entries (holiday or weekly off) falling within the given date range."""
    rows = frappe.db.sql(
        """
        SELECT parent, holiday_date
        FROM `tabHoliday`
        WHERE parentfield = 'holidays'
        AND parenttype = 'Holiday List'
        AND holiday_date BETWEEN %(start)s AND %(end)s
        """,
        {"start": start_date, "end": end_date},
        as_dict=True,
    )

    holiday_map = {}
    for r in rows:
        holiday_map.setdefault(r.parent, {})[getdate(r.holiday_date)] = True
    return holiday_map


def resolve_holiday_list_for_date(current_date, current_holiday_list, work_history_rows, date_of_joining, anchors, today):
    """Resolves which Holiday List applies to a date with no Attendance
    record. Past dates, in priority order: 1st, the employee's Internal Work
    History period covering that date (a row with no from_date is treated as
    starting on the employee's date_of_joining); 2nd, the Holiday List of the
    closest later Attendance record. Today/future dates use the employee's
    current Holiday List."""
    if current_date >= today:
        return current_holiday_list

    wh_holiday_list = find_work_history_holiday_list(current_date, work_history_rows, date_of_joining)
    if wh_holiday_list:
        return wh_holiday_list

    for anchor_date, anchor_holiday_list in anchors:
        if anchor_date > current_date:
            return anchor_holiday_list

    return current_holiday_list


def is_holiday_or_weekend(current_date, holiday_list_name, holiday_map) -> bool:
    if not holiday_list_name:
        return False
    return current_date in holiday_map.get(holiday_list_name, {})


def get_data(filters):
    data = []

    employee_details = get_employee_details(filters)
    employee_ids = list(employee_details.keys())

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

    checkin_tags = get_local_checkin_tags(employee_ids, start_date.date(), end_date.date())

    attendance_records = frappe.get_all('Attendance', filters={
        'attendance_date': ['between', [start_date_str, end_date_str]],
        'employee': ['in', employee_ids],
        'docstatus': 1
    }, fields=['employee', 'employee_name', 'attendance_date', 'in_time', 'out_time', 'status', 'attendance_request'])

    attendance_dict = {}
    for record in attendance_records:
        in_time = record['in_time'].strftime('%H:%M') if record['in_time'] else None
        out_time = record['out_time'].strftime('%H:%M') if record['out_time'] else None
        attendance_dict.setdefault(record['employee'], {})[record['attendance_date']] = {
            'in_time': in_time,
            'out_time': out_time,
            'status': record['status'],
            'attendance_request': record.get('attendance_request'),
        }

    work_history_map = get_work_history_map(employee_ids)
    holiday_anchors = get_holiday_anchors(filters, employee_ids)
    holiday_map = get_holiday_map(start_date.date(), end_date.date())

    serial_number = 1
    for employee in employee_ids:
        details = employee_details[employee]
        is_inactive = details.status and details.status != 'Active'
        employee_display_name = (
            f"{details.employee_name} (Inactive)"
            if filters.get('is_active') and is_inactive
            else details.employee_name
        )

        row = {
            'serial_number': serial_number,
            'employee_id': employee,
            'employee_name': employee_display_name
        }

        current_holiday_list = details.holiday_list
        work_history_rows = work_history_map.get(employee, [])
        date_of_joining = details.date_of_joining
        anchors = holiday_anchors.get(employee, [])
        draft_request = get_draft_requests(filters, employee)

        current_date = start_date
        while current_date <= end_date:
            is_today = current_date.date() == today

            # Check for live check-in data first for today
            if is_today and employee in checkin_data:
                checkins = checkin_data[employee]
                in_times = [c['time'] for c in checkins if c['type'] == 'IN' and c['time'] is not None]
                out_times = ''

                if in_times or out_times:
                    in_val = convert_to_am_pm(in_times[0]) if in_times else '-'
                    if in_times:
                        in_tag = local_tag(checkin_tags, employee, current_date.date(), "IN")
                        if in_tag:
                            in_val = f"{in_val} ({in_tag})"
                    row[f'in_{current_date.day}'] = format_with_color(in_val, 'green')
                    row[f'out_{current_date.day}'] = format_with_color(
                        convert_to_am_pm(out_times[-1]) if out_times else '-',
                        'green'
                    )
                    current_date += timedelta(days=1)
                    continue

            # Existing attendance processing
            attendance = attendance_dict.get(employee, {}).get(current_date.date(), None)

            if attendance and attendance['status'] == 'Present':
                # A submitted Attendance Request on the record takes
                # priority over the local-checkin (IN/OUT office) tag.
                ar_tag = 'AR' if attendance.get('attendance_request') else None

                in_val = convert_to_am_pm(attendance['in_time']) if attendance['in_time'] else 'P'
                in_tag = ar_tag or (
                    local_tag(checkin_tags, employee, current_date.date(), "IN") if attendance['in_time'] else None
                )
                if in_tag:
                    in_val = f"{in_val} ({in_tag})"

                out_val = convert_to_am_pm(attendance['out_time']) if attendance['out_time'] else 'P'
                out_tag = ar_tag or (
                    local_tag(checkin_tags, employee, current_date.date(), "OUT") if attendance['out_time'] else None
                )
                if out_tag:
                    out_val = f"{out_val} ({out_tag})"

                row[f'in_{current_date.day}'] = format_with_color(in_val, 'green')
                row[f'out_{current_date.day}'] = format_with_color(out_val, 'green')
            elif attendance and attendance['status'] == 'Work From Home':
                row[f'in_{current_date.day}'] = format_with_color('WFH', 'blue')
                row[f'out_{current_date.day}'] = format_with_color('WFH', 'blue')
            elif attendance and attendance['status'] == 'On Leave':
                row[f'in_{current_date.day}'] = format_with_color('L', 'orange')
                row[f'out_{current_date.day}'] = format_with_color('L', 'orange')
            else:
                holiday_list_name = resolve_holiday_list_for_date(
                    current_date.date(), current_holiday_list, work_history_rows,
                    date_of_joining, anchors, today
                )
                if is_holiday_or_weekend(current_date.date(), holiday_list_name, holiday_map):
                    row[f'in_{current_date.day}'] = format_with_color('H/W', 'brown')
                    row[f'out_{current_date.day}'] = format_with_color('H/W', 'brown')
                else:
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
    """Fetches draft leave applications and attendance requests for a single
    employee. The employee is already vetted against the active/relieved-in-
    range condition at the employee-list level, so no further status check
    is needed here."""
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
            & (AttendanceRequest.workflow_state == "Applied")
            & (AttendanceRequest.employee == employee)
            & (Extract("month", AttendanceRequest.from_date) == filters.month)
            & (Extract("year", AttendanceRequest.from_date) == filters.year)
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
