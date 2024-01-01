# Copyright (c) 2023, Shaid Azmin and contributors
# For license information, please see license.txt

# import frappe


def execute(filters=None):
	columns, data = [], []
	return columns, data
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from datetime import datetime

from hrms.hr.doctype.leave_application.leave_application import get_leave_details




def execute(filters=None):
    leave_types = frappe.db.sql_list(
        "select name from `tabLeave Type` order by name asc")

    columns = get_columns(leave_types)
    data = get_data(filters, leave_types)

    return columns, data


def get_columns(leave_types):
	columns = [
		_("Employee") + ":Link/Employee:150",
		_("Employee Name") + "::200",
		_("Department") + ":Link/Department:150",
	]

	for leave_type in leave_types:
		columns.append(_(leave_type + "(Available)") + ":Float:170")

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
        conditions.update(
            {"excel_parent_department": filters.get("excel_department")})
    if filters.get("excel_section"):
        conditions.update({"excel_hr_section": filters.get("excel_section")})
    if filters.get("excel_sub_section"):
        conditions.update(
            {"excel_hr_sub_section": filters.get("excel_sub_section")})
    if filters.get("excel_job_location"):
        conditions.update(
            {"excel_job_location": filters.get("excel_job_location")})
    return conditions


# ... (previous code)

def get_data(filters, leave_types):
    user = frappe.session.user
    conditions = get_conditions(filters)

    active_employees = frappe.get_list(
        "Employee",
        filters=conditions,
        fields=["name", "employee_name", "department", "user_id"],
    )
    print(active_employees)
    get_last_date=get_last_day_of_year(filters.year)
    data = []
    for employee in active_employees:
        row = [employee.name, employee.employee_name, employee.department]
        available_leave = get_leave_details(employee.name, get_last_date)
        for leave_type in leave_types:
            remaining = 0
            if leave_type in available_leave["leave_allocation"]:
                remaining = available_leave["leave_allocation"][leave_type]["remaining_leaves"]
                if leave_type == "Special Leave" :
                    remaining = 0
            row += [remaining]

        data.append(row)
    return data

# ... (rest of your code)

# def get_data(filters, leave_types):
#     user = frappe.session.user
#     conditions = get_conditions(filters)

#     active_employees = frappe.get_list(
#         "Employee",
#         filters=conditions,
#         fields=["name", "employee_name", "department", "user_id"],
#     )

#     data = []
#     for employee in active_employees:
#         row = [employee.name, employee.employee_name, employee.department]
#         available_leave = get_leave_details(employee.name, filters.date)

#         # Initialize total used leave for each employee
#         total_used_leave = {leave_type: 0 for leave_type in leave_types}

#         # Fetch leave applications for the employee
#         leave_applications = frappe.get_all(
#             "Leave Application",
#             filters={
#                 "employee": employee.name,
#                 "status": ("!=", "Cancelled"),
#                 "from_date": (">=", filters.date),
#             },
#             fields=["leave_type", "total_leave_days"],
#         )

#         # Calculate total used leave for each leave type
#         for leave_application in leave_applications:
#             leave_type = leave_application.leave_type
#             total_leave_days = leave_application.total_leave_days
#             total_used_leave[leave_type] += total_leave_days

#         # Append total used leave for each leave type to the row
#         for leave_type in leave_types:
#             row.append(total_used_leave[leave_type])

#         data.append(row)

#     return data
def get_last_day_of_year(year):
    # Construct the last day of the year
    last_day_of_year = frappe.utils.getdate(f"{year}-12-31")
    return last_day_of_year