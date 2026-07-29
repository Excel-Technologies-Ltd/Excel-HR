# Copyright (c) 2026, Shaid Azmin and contributors
# License: GNU General Public License v3. See license.txt


from datetime import timedelta
from typing import Dict, List, Optional, Set, Tuple

import frappe
from frappe import _
from frappe.utils import getdate

Filters = frappe._dict

COUNT_FIELDS = [
    "present",
    "leave",
    "weekly_off",
    "holiday",
    "wfh",
    "leave_application",
    "ar_application",
    "absent",
]

METRIC_ROWS = [
    ("present", "P"),
    ("present_percent", "P%"),
    ("leave", "L"),
    ("leave_percent", "L%"),
    ("weekly_off", "WO"),
    ("weekly_off_percent", "WO%"),
    ("holiday", "H"),
    ("holiday_percent", "H%"),
    ("wfh", "WFH"),
    ("wfh_percent", "WFH%"),
    ("leave_application", "L.App"),
    ("leave_application_percent", "L.App%"),
    ("ar_application", "AR.App"),
    ("ar_application_percent", "AR.App%"),
    ("absent", "A"),
    ("absent_percent", "A%"),
    ("total", "Total Count"),
]


def execute(filters: Optional[Filters] = None) -> Tuple:
    filters = frappe._dict(filters or {})

    date_range = filters.get("date_range")
    if not date_range or not date_range[0] or not date_range[1]:
        frappe.throw(_("Please select a Date Range."))

    filters.date_range = [getdate(date_range[0]), getdate(date_range[1])]

    columns = get_columns(filters)
    data = get_data(filters)

    return columns, data, get_message(), None


def get_message() -> str:
    legend = [
        ("P", _("Present"), "green"),
        ("L", _("Leave"), "#318AD8"),
        ("WO", _("Weekly Off"), "brown"),
        ("H", _("Holiday"), "brown"),
        ("WFH", _("Work From Home"), "green"),
        ("L.App", _("Leave Application"), "#318AD8"),
        ("AR.App", _("Attendance Req. Application"), "orange"),
        ("A", _("Absent"), "red"),
    ]

    message = "<div style='display:flex;flex-wrap:wrap; margin-bottom: 10px;'>"
    for abbr, label, color in legend:
        message += f"""
            <span style='font-size:10px; color:{color}; padding-right: 12px; padding-left: 5px; margin-right: 3px; display: inline-block;'>
                &#8718; {abbr} = {label}
            </span>
        """
    message += "</div>"
    return message


def get_columns(filters: Filters) -> List[Dict]:
    from_date, to_date = filters.date_range

    columns = [
        {
            "label": _("Metric"), 
            "fieldname": "metric", 
            "fieldtype": "Data", 
            "width": 110,
        }
    ]

    current_date = from_date
    idx = 1
    while current_date <= to_date:
        columns.append(
            {
                "label": current_date.strftime("%d-%b-%Y"),
                "fieldname": f"day_{idx}",
                "fieldtype": "Data",
                "width": 90,
            }
        )
        current_date += timedelta(days=1)
        idx += 1

    return columns


def get_employees() -> List[Dict]:
    Employee = frappe.qb.DocType("Employee")
    return (
        frappe.qb.from_(Employee)
        .select(
            Employee.name,
            Employee.company,
            Employee.holiday_list,
            Employee.date_of_joining,
            Employee.relieving_date,
        )
    ).run(as_dict=True)


def get_attendance_map(employee_ids: List[str], from_date, to_date) -> Dict[str, Dict]:
    if not employee_ids:
        return {}

    Attendance = frappe.qb.DocType("Attendance")
    rows = (
        frappe.qb.from_(Attendance)
        .select(Attendance.employee, Attendance.attendance_date, Attendance.status)
        .where(
            (Attendance.docstatus == 1)
            & Attendance.employee.isin(employee_ids)
            & (Attendance.attendance_date >= from_date)
            & (Attendance.attendance_date <= to_date)
        )
    ).run(as_dict=True)

    attendance_map: Dict[str, Dict] = {}
    for r in rows:
        attendance_map.setdefault(r.employee, {})[getdate(r.attendance_date)] = r.status
    return attendance_map


def get_holiday_map(holiday_lists: List[str], from_date, to_date) -> Dict[str, Dict]:
    holiday_lists = [h for h in holiday_lists if h]
    if not holiday_lists:
        return {}

    Holiday = frappe.qb.DocType("Holiday")
    rows = (
        frappe.qb.from_(Holiday)
        .select(Holiday.parent, Holiday.holiday_date, Holiday.weekly_off)
        .where(
            Holiday.parent.isin(holiday_lists)
            & (Holiday.holiday_date >= from_date)
            & (Holiday.holiday_date <= to_date)
        )
    ).run(as_dict=True)

    holiday_map: Dict[str, Dict] = {}
    for r in rows:
        holiday_map.setdefault(r.parent, {})[getdate(r.holiday_date)] = bool(r.weekly_off)
    return holiday_map


def get_date_span_map(rows: List[Dict], from_date, to_date) -> Dict[str, Set]:
    days_map: Dict[str, Set] = {}
    for r in rows:
        start = max(getdate(r.from_date), from_date)
        end = min(getdate(r.to_date), to_date)
        d = start
        while d <= end:
            days_map.setdefault(r.employee, set()).add(d)
            d += timedelta(days=1)
    return days_map


def get_leave_application_days(employee_ids: List[str], from_date, to_date) -> Dict[str, Set]:
    if not employee_ids:
        return {}

    LeaveApplication = frappe.qb.DocType("Leave Application")
    rows = (
        frappe.qb.from_(LeaveApplication)
        .select(LeaveApplication.employee, LeaveApplication.from_date, LeaveApplication.to_date)
        .where(
            (LeaveApplication.docstatus == 0)
            & (LeaveApplication.status == "Open")
            & LeaveApplication.employee.isin(employee_ids)
            & (LeaveApplication.from_date <= to_date)
            & (LeaveApplication.to_date >= from_date)
        )
    ).run(as_dict=True)

    return get_date_span_map(rows, from_date, to_date)


def get_attendance_request_days(employee_ids: List[str], from_date, to_date) -> Dict[str, Set]:
    if not employee_ids:
        return {}

    AttendanceRequest = frappe.qb.DocType("Attendance Request")
    rows = (
        frappe.qb.from_(AttendanceRequest)
        .select(AttendanceRequest.employee, AttendanceRequest.from_date, AttendanceRequest.to_date)
        .where(
            (AttendanceRequest.docstatus == 0)
            & (AttendanceRequest.workflow_state == "Applied")
            & AttendanceRequest.employee.isin(employee_ids)
            & (AttendanceRequest.from_date <= to_date)
            & (AttendanceRequest.to_date >= from_date)
        )
    ).run(as_dict=True)

    return get_date_span_map(rows, from_date, to_date)


def format_count(value: float):
    # Returning clean primitive types prevents Frappe from treating valid zeros as empty strings
    return int(value) if value == int(value) else round(value, 2)


def get_data(filters: Filters) -> List[List]:
    from_date, to_date = filters.date_range

    employees = get_employees()
    if not employees:
        return []

    employee_ids = [emp.name for emp in employees]
    companies = {emp.company for emp in employees if emp.company}
    default_holiday_list_map = {c: frappe.get_cached_value("Company", c, "default_holiday_list") for c in companies}

    attendance_map = get_attendance_map(employee_ids, from_date, to_date)
    holiday_lists = {emp.holiday_list for emp in employees if emp.holiday_list} | {
        h for h in default_holiday_list_map.values() if h
    }
    holiday_map = get_holiday_map(list(holiday_lists), from_date, to_date)
    leave_application_days = get_leave_application_days(employee_ids, from_date, to_date)
    attendance_request_days = get_attendance_request_days(employee_ids, from_date, to_date)

    daily_counts: Dict = {}
    current_date = from_date
    while current_date <= to_date:
        daily_counts[current_date] = dict.fromkeys(COUNT_FIELDS, 0.0)
        current_date += timedelta(days=1)

    for emp in employees:
        join_date = getdate(emp.date_of_joining) if emp.date_of_joining else None
        relieving_date = getdate(emp.relieving_date) if emp.relieving_date else None
        default_holiday_list = default_holiday_list_map.get(emp.company)
        holidays = holiday_map.get(emp.holiday_list or default_holiday_list, {})
        emp_attendance = attendance_map.get(emp.name, {})
        emp_leave_app_days = leave_application_days.get(emp.name, set())
        emp_ar_app_days = attendance_request_days.get(emp.name, set())

        current_date = from_date
        while current_date <= to_date:
            if join_date and current_date < join_date:
                current_date += timedelta(days=1)
                continue
            if relieving_date and current_date > relieving_date:
                current_date += timedelta(days=1)
                continue

            counts = daily_counts[current_date]
            status = emp_attendance.get(current_date)

            if status == "Present":
                counts["present"] += 1
            elif status == "Absent":
                counts["absent"] += 1
            elif status == "Half Day":
                counts["present"] += 0.5
                counts["leave"] += 0.5
            elif status == "Work From Home":
                counts["wfh"] += 1
            elif status == "On Leave":
                counts["leave"] += 1
            elif current_date in holidays:
                if holidays[current_date]:
                    counts["weekly_off"] += 1
                else:
                    counts["holiday"] += 1
            elif current_date in emp_leave_app_days:
                counts["leave_application"] += 1
            elif current_date in emp_ar_app_days:
                counts["ar_application"] += 1
            else:
                counts["absent"] += 1

            current_date += timedelta(days=1)

    # SWITCHED TO A LIST OF LISTS: guarantees column order and prevents missing cells 
    rows = []
    for field, label in METRIC_ROWS:
        row = [label]  # First column is always the metric label
        
        current_date = from_date
        while current_date <= to_date:
            counts = daily_counts[current_date]
            total_for_day = sum(counts.values())
            
            if field == "total":
                row.append(format_count(total_for_day))
            elif field.endswith("_percent"):
                base_field = field[: -len("_percent")]
                pct = (counts[base_field] / total_for_day * 100) if total_for_day else 0.0
                row.append(f"{round(pct)}%")
            else:
                row.append(format_count(counts[field]))

            current_date += timedelta(days=1)

        rows.append(row)

    return rows