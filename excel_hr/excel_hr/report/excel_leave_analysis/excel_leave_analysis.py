# Copyright (c) 2023, Shaid Azmin and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime
from hrms.hr.doctype.leave_application.leave_application import get_leave_details

def execute(filters=None):
    leave_types = frappe.db.sql_list(
        "select name from `tabLeave Type` order by name asc")
    
    columns = get_columns(leave_types, filters)
    data = get_data(filters, leave_types)

    return columns, data

def get_columns(leave_types, filters):
    columns = [
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 120},
    ]

    selected_leave_types = filters.get("leave_type", [])

    for leave_type in leave_types:
        if not selected_leave_types or leave_type in selected_leave_types:
            columns.extend([
                {
                    "label": _(f"{leave_type} (Allocated)"), 
                    "fieldname": f"{leave_type.lower()}_allocated",
                    "fieldtype": "Float",
                    "width": 120
                },
                {
                    "label": _(f"{leave_type} (Used)"), 
                    "fieldname": f"{leave_type.lower()}_used",
                    "fieldtype": "Float",
                    "width": 100
                },
                {
                    "label": _(f"{leave_type} (Pending)"), 
                    "fieldname": f"{leave_type.lower()}_pending",
                    "fieldtype": "Float",
                    "width": 100
                },
                {
                    "label": _(f"{leave_type} (Available)"), 
                    "fieldname": f"{leave_type.lower()}_available",
                    "fieldtype": "Float",
                    "width": 100,
                    "css": "background-color: #f2f2f2;" if leave_type == "Special Leave" else ""
                }
            ])
    
    return columns

def get_conditions(filters):
    conditions = {
        "company": filters.company,
    }
    if filters.get("employee_status"):
        conditions.update({"status": filters.get("employee_status")})
    if filters.get("department"):
        conditions.update({"department": filters.get("department")})
    if filters.get("employee"):
        conditions.update({"employee": ["in", filters.get("employee")]})
    if filters.get("excel_department"):
        conditions.update({"excel_parent_department": filters.get("excel_department")})
    if filters.get("excel_section"):
        conditions.update({"excel_hr_section": filters.get("excel_section")})
    if filters.get("excel_sub_section"):
        conditions.update({"excel_hr_sub_section": filters.get("excel_sub_section")})
    if filters.get("custom_job_location"):
        conditions.update({"custom_job_location": filters.get("custom_job_location")})
    if filters.get("custom_reporting_location"):
        conditions.update({"custom_reporting_location": filters.get("custom_reporting_location")})        
    return conditions

def get_data(filters, leave_types):
    conditions = get_conditions(filters)
    current_date = datetime.now()
    
    # Set date range for the report
    if filters.get("from_date") and filters.get("to_date"):
        start_date = filters.from_date
        end_date = filters.to_date
    else:
        # Default to current year if dates not specified
        start_date = current_date.replace(month=1, day=1).strftime('%Y-%m-%d')
        end_date = current_date.replace(month=12, day=31).strftime('%Y-%m-%d')

    active_employees = frappe.get_list(
        "Employee",
        filters=conditions,
        fields=["name", "employee_name", "department", "user_id"],
    )

    data = []
    for employee in active_employees:
        row = {
            "employee": employee.name,
            "employee_name": employee.employee_name,
            "department": employee.department,
        }

        # Initialize leave data dictionaries
        leave_data = {
            "allocated": {lt: 0 for lt in leave_types},
            "used": {lt: 0 for lt in leave_types},
            "pending": {lt: 0 for lt in leave_types},
            "available": {lt: 0 for lt in leave_types}
        }

        # Get leave allocations
        allocations = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee.name,
                "docstatus": 1,
                "from_date": ("<=", end_date),
                "to_date": (">=", start_date)
            },
            fields=["leave_type", "total_leaves_allocated"]
        )

        # Get approved leave applications
        approved_leaves = frappe.get_all(
            "Leave Application",
            filters={
                "employee": employee.name,
                "status": "Approved",
                "docstatus": 1,
                "from_date": ("<=", end_date),
                "to_date": (">=", start_date)
            },
            fields=["leave_type", "total_leave_days"]
        )

        # Get pending leave applications
        pending_leaves = frappe.get_all(
            "Leave Application",
            filters={
                "employee": employee.name,
                "docstatus": 0,  # Pending applications
                "from_date": ("<=", end_date),
                "to_date": (">=", start_date)
            },
            fields=["leave_type", "total_leave_days"]
        )

        # Process allocations
        for alloc in allocations:
            leave_type = alloc.leave_type
            if leave_type in leave_data["allocated"]:
                if leave_type == "Special Leave":
                    leave_data["allocated"][leave_type] = 0
                else:
                    leave_data["allocated"][leave_type] += alloc.total_leaves_allocated

        # Process approved leaves
        for app in approved_leaves:
            leave_type = app.leave_type
            if leave_type in leave_data["used"]:
                leave_data["used"][leave_type] += app.total_leave_days

        # Process pending leaves
        for pend in pending_leaves:
            leave_type = pend.leave_type
            if leave_type in leave_data["pending"]:
                leave_data["pending"][leave_type] += pend.total_leave_days

        # Calculate available leaves
        for leave_type in leave_types:
            if leave_type == "Annual Leave":
                leave_data["available"][leave_type] = max(
                    leave_data["allocated"][leave_type] - 
                    (leave_data["used"][leave_type] + leave_data["pending"][leave_type]),
                    0
                )
            elif leave_type == "Special Leave":
                leave_data["available"][leave_type] = 0
            else:
                leave_data["available"][leave_type] = max(
                    leave_data["allocated"][leave_type] - leave_data["used"][leave_type],
                    0
                )

            # Add to row data
            row.update({
                f"{leave_type.lower()}_allocated": leave_data["allocated"][leave_type],
                f"{leave_type.lower()}_used": leave_data["used"][leave_type],
                f"{leave_type.lower()}_pending": leave_data["pending"][leave_type],
                f"{leave_type.lower()}_available": leave_data["available"][leave_type],
            })

        data.append(row)

    return data