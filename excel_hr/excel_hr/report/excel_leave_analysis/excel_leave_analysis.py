# Copyright (c) 2023, Shaid Azmin and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe import _
from datetime import datetime, timedelta
from hrms.hr.doctype.leave_application.leave_application import get_leave_details

def execute(filters=None):
    leave_types = frappe.db.sql_list(
        "select name from `tabLeave Type` order by name asc")
    # Set your custom column name prefix here
    column_name_prefix = "MyPrefix"

    columns = get_columns(leave_types,filters, column_name_prefix)
    data = get_data(filters, leave_types, column_name_prefix)

    return columns, data
# def get_columns(leave_types, column_name_prefix=""):
#     columns = [
#         {"fieldname": "employee", "label": _("Employee"), "fieldtype": "Link", "options": "Employee", "width": 150},
#         {"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data", "width": 200},
#         {"fieldname": "department", "label": _("Department"), "fieldtype": "Link", "options": "Department", "width": 150},
#     ]

#     for leave_type in leave_types:
#         # Assume you have CSS classes named 'annual-leave' and 'special-leave' for Annual Leave and Special Leave
#         bg_color = "#ff0000" if leave_type.lower() == "annual leave" else "#00ff00" if leave_type.lower() == "special leave" else "#ffffff"
#         columns.append({
#             "fieldname": leave_type.lower() + "_available",
#             "label": _("{0} (Available)").format(leave_type),
#             "fieldtype": "Float",
#             "width": 170,
#              "css": {"background-color": "red"},  # Set CSS class dynamically
#         })

#         columns.append({
#             "fieldname": leave_type.lower() + "_used",
#             "label": _("{0} (Used)").format(leave_type),
#             "fieldtype": "Float",
#             "width": 170,
#             "css": {"background-color": bg_color}, # Set CSS class dynamically
#         })

#         columns.append({
#             "fieldname": leave_type.lower() + "_total",
#             "label": _("{0} (Total)").format(leave_type),
#             "fieldtype": "Float",
#             "width": 170,
#             "css": {"background-color": bg_color},  # Set CSS class dynamically
#         })

#     return columns
def get_columns(leave_types, filters, column_name_prefix=""):
    columns = [
        _("Employee") + ":Link/Employee:150",
        _("Employee Name") + "::200",
        _("Department") + ":Link/Department:150",
    ]

    selected_leave_types = filters.get("leave_type", [])

    if filters.get("leave_type"):
        for leave_type in leave_types:
            if not selected_leave_types or leave_type in selected_leave_types:
                columns.append(_(leave_type + "(Available)") + ":Float:170")
                columns.append(_(leave_type + "(Used)") + ":Float:170")  # Add used leave column
                columns.append(_(leave_type + "(Allocated)") + ":Float:170")
    else:
         for leave_type in leave_types:
                columns.append(_(leave_type + "(Available)") + ":Float:170")
                columns.append(_(leave_type + "(Used)") + ":Float:170")  # Add used leave column
                columns.append(_(leave_type + "(Allocated)") + ":Float:170")
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
    if filters.get("excel_job_location"):
        conditions.update({"excel_job_location": filters.get("excel_job_location")})
    return conditions

def get_data(filters, leave_types, column_name_prefix=""):
    user = frappe.session.user
    conditions = get_conditions(filters)
    current_date = datetime.now()

    # Set start and end dates for the full year
    start_of_year = current_date.replace(month=1, day=1)
    end_of_year = current_date.replace(month=12, day=31)

    active_employees = frappe.get_list(
        "Employee",
        filters=conditions,
        fields=["name", "employee_name", "department", "user_id"],
    )

    data = []
    for employee in active_employees:
        print(filters.date)
        row = [employee.name, employee.employee_name, employee.department]
        available_leave = get_leave_details(employee.name, filters.date)
        print(available_leave)
        # Use end_of_year for leave details retrieval

        # Initialize total used leave, total available leave, and total leave for each employee
        total_used_leave = {leave_type: 0 for leave_type in leave_types}
        total_available_leave = {leave_type: 0 for leave_type in leave_types}
        total_allocated_leave = {leave_type: 0 for leave_type in leave_types}

        # Fetch leave applications for the employee
        leave_applications = frappe.get_all(
            "Leave Application",
            filters={
                "employee": employee.name,
                "status": ("=", "Approved"),
                "from_date": (">=", start_of_year),
                "to_date": ("<=", end_of_year),
            },
            fields=["leave_type", "total_leave_days"],
        )
        leave_allocations = frappe.get_all(
            "Leave Allocation",
            filters={
                "employee": employee.name,
                "docstatus": ("=", "1"),
                "from_date": (">=", start_of_year),
                "to_date": ("<=", end_of_year),
            },
            fields=["leave_type", "total_leaves_allocated"],
        ) 
        
        for allocation in leave_allocations:
            leave_type = allocation.leave_type
            total_leave_allocated = allocation.total_leaves_allocated
            total_allocated_leave[leave_type] += total_leave_allocated 
            if leave_type == "Special Leave":
                total_allocated_leave[leave_type] = 0 
            print(total_allocated_leave[leave_type])      
        # Calculate total used leave for each leave type
        for leave_application in leave_applications:
            leave_type = leave_application.leave_type
            total_leave_days = leave_application.total_leave_days
            total_used_leave[leave_type] += total_leave_days
            
            # total_available_leave = total_allocated_leave[leave_type] - total_used_leave[leave_type]    

        # Calculate total available leave for each leave type
        for leave_type in leave_types:
            remaining = 0
           
            if leave_type in available_leave["leave_allocation"]:
                remaining = available_leave["leave_allocation"][leave_type]["remaining_leaves"]
                if leave_type == "Special Leave" :
                    remaining = 0                
            total_available_leave[leave_type] = remaining 
            # + total_used_leave[leave_type]

            
        #     print(total_available_leave)
        #     # if leave_type == "Special Leave" :
        #     #     total_leave=0

            # Append total available leave, total used leave, and total leave for each leave type to the row
            row.append(total_available_leave[leave_type])
            row.append(total_used_leave[leave_type])
            row.append(total_allocated_leave[leave_type])

        data.append(row)

    return data
...



