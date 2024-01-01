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
    # leave_types = frappe.db.sql_list(
    #     "select name from `tabLeave Type` order by name asc")
    leave_types=['Annual Leave','Special Leave']
    columns = get_columns(leave_types)
    data = get_data(filters, leave_types)

    return columns, data


def get_columns(leave_types):
	columns = [
		_("Employee") + ":Link/Employee:150",
		_("Employee Name") + "::200",
		_("Department") + ":Link/Department:150",
	]
	if "Annual Leave" in leave_types:
		columns.append(_("Annual Leave (Casual)") + ":Float:175")
		columns.append(_("Annual Leave (Medical)") + ":Float:175")
	if "Special Leave" in leave_types:
		columns.append(_("Special Leave (Casual)") + ":Float:175")
		columns.append(_("Special Leave (Medical)") + ":Float:175")
	return columns

def get_january_first():
    current_year = datetime.now().year
    january_first = datetime(current_year, 1, 1)
    formatted_date = january_first.strftime("%Y-%m-%d")

    return formatted_date

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



def get_data(filters, leave_types):
    data=[]
    conditions = get_conditions(filters) 
    active_employees = frappe.get_list(
        "Employee",
        filters=conditions,
        fields=["name", "employee_name", "department", "user_id"],
    )
    for employee in active_employees:
        row = [employee.name, employee.employee_name, employee.department]
        available_leave = get_leave_details(employee.name, filters.date)

        # Initialize total used leave for each employee
        total_used_leave = {leave_type: 0 for leave_type in leave_types}
        total_used_leave["Annual Casual Leave"] = 0
        total_used_leave["Annual Medical Leave"] = 0
        total_used_leave["Special Casual Leave"] = 0
        total_used_leave["Special Medical Leave"] = 0

        # Fetch leave applications for the employee
        leave_applications = frappe.get_all(
            "Leave Application",
            filters={
                "employee": employee.name,
                "status": ("=", "Approved"),
                "from_date": (">=", filters.date_range[0]),
                "to_date": ("<=", filters.date_range[1]),
                "leave_type": ("in", leave_types)
            },
            fields=["leave_type", "excel_leave_category", "total_leave_days"],
        )

        # Calculate total used leave for each leave type
        for leave_application in leave_applications:
            leave_type = leave_application.leave_type
            total_leave_days = leave_application.total_leave_days
            total_used_leave[leave_type] += total_leave_days

            # Check for specific leave types and categories
            if leave_type == "Annual Leave":
                if leave_application.excel_leave_category == "Casual":
                    total_used_leave["Annual Casual Leave"] += total_leave_days
                elif leave_application.excel_leave_category == "Medical":
                    total_used_leave["Annual Medical Leave"] += total_leave_days
            elif leave_type == "Special Leave":
                if leave_application.excel_leave_category == "Casual":
                    total_used_leave["Special Casual Leave"] += total_leave_days
                elif leave_application.excel_leave_category == "Medical":
                    total_used_leave["Special Medical Leave"] += total_leave_days

        # Append total used leave for each leave type to the row
        for leave_type in leave_types:
            row.append(total_used_leave[leave_type])

        # Add specific values for each leave type and category
        if "Annual Leave" in leave_types:
            row.append(total_used_leave["Annual Casual Leave"])
            row.append(total_used_leave["Annual Medical Leave"])
        if "Special Leave" in leave_types:
            row.append(total_used_leave["Special Casual Leave"])
            row.append(total_used_leave["Special Medical Leave"])

        data.append(row)

    return data