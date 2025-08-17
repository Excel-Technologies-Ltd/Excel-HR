# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from itertools import groupby
import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate

def execute(filters=None):
    if not filters:
        filters = {}

    if filters.to_date <= filters.from_date:
        frappe.throw(_('"From Date" must be earlier than "To Date"'))

    columns = get_columns()
    data = get_custom_leave_data(filters)
    charts = get_chart_data(data, filters)
    
    return columns, data, None, charts

def get_columns():
    return [
        {
            "label": _("Leave Type"),
            "fieldtype": "Link",
            "fieldname": "leave_type",
            "width": 200,
            "options": "Leave Type",
        },
        {
            "label": _("Employee"),
            "fieldtype": "Link",
            "fieldname": "employee",
            "width": 100,
            "options": "Employee",
        },
        {
            "label": _("Employee Name"),
            "fieldtype": "Dynamic Link",
            "fieldname": "employee_name",
            "width": 100,
            "options": "employee",
        },
        {
            "label": _("Opening Balance"),
            "fieldtype": "float",
            "fieldname": "opening_balance",
            "width": 150,
        },
        {
            "label": _("New Leave(s) Allocated"),
            "fieldtype": "float",
            "fieldname": "leaves_allocated",
            "width": 200,
        },
        {
            "label": _("Leave(s) Taken"),
            "fieldtype": "float",
            "fieldname": "leaves_taken",
            "width": 150,
        },
        {
            "label": _("Leave(s) Expired"),
            "fieldtype": "float",
            "fieldname": "leaves_expired",
            "width": 150,
        },
        {
            "label": _("Closing Balance"),
            "fieldtype": "float",
            "fieldname": "closing_balance",
            "width": 150,
        },
    ]

def get_custom_leave_data(filters):
    # Get all active employees based on filters
    employee_condition = ""
    if filters.get("employee"):
        employee_condition = f"AND e.name = '{filters.employee}'"
    elif filters.get("department"):
        employee_condition = f"AND e.department = '{filters.department}'"
    elif filters.get("company"):
        employee_condition = f"AND e.company = '{filters.company}'"
    
    status_condition = ""
    if filters.get("employee_status"):
        status_condition = f"AND e.status = '{filters.employee_status}'"
    
    # Main query to get leave balance data
    query = f"""
        SELECT 
            lt.name as leave_type,
            e.name as employee,
            e.employee_name,
            -- Opening balance (all allocations before period minus leaves taken before period)
            IFNULL((
                SELECT SUM(IFNULL(alloc.leaves, 0)) - IFNULL((
                    SELECT SUM(ABS(taken.leaves))
                    FROM `tabLeave Ledger Entry` taken
                    WHERE taken.docstatus = 1
                    AND taken.employee = e.name
                    AND taken.leave_type = lt.name
                    AND taken.transaction_type = 'Leave Application'
                    AND taken.from_date < '{filters.from_date}'
                ), 0)
                FROM `tabLeave Ledger Entry` alloc
                WHERE alloc.docstatus = 1
                AND alloc.employee = e.name
                AND alloc.leave_type = lt.name
                AND alloc.transaction_type = 'Leave Allocation'
                AND alloc.from_date < '{filters.from_date}'
                AND alloc.is_expired = 0
            ), 0) as opening_balance,
            
            -- New allocations during period
            IFNULL((
                SELECT SUM(IFNULL(new_alloc.leaves, 0))
                FROM `tabLeave Ledger Entry` new_alloc
                WHERE new_alloc.docstatus = 1
                AND new_alloc.employee = e.name
                AND new_alloc.leave_type = lt.name
                AND new_alloc.transaction_type = 'Leave Allocation'
                AND new_alloc.from_date >= '{filters.from_date}'
                AND new_alloc.from_date <= '{filters.to_date}'
                AND new_alloc.is_expired = 0
            ), 0) as leaves_allocated,
            
            -- Leaves taken during period (total leave days, regardless of include_holiday)
            IFNULL((
                SELECT SUM(IFNULL(taken.total_leave_days, 0))  -- Sum of total_leave_days for taken leave
                FROM `tabLeave Ledger Entry` taken
                WHERE taken.docstatus = 1
                AND taken.employee = e.name
                AND taken.leave_type = lt.name
                AND taken.transaction_type = 'Leave Application'
                AND taken.from_date >= '{filters.from_date}'
                AND taken.to_date <= '{filters.to_date}'
            ), 0) as leaves_taken,
            
            -- Leaves expired during period
            IFNULL((
                SELECT SUM(IFNULL(expired.leaves, 0))
                FROM `tabLeave Ledger Entry` expired
                WHERE expired.docstatus = 1
                AND expired.employee = e.name
                AND expired.leave_type = lt.name
                AND expired.transaction_type = 'Leave Allocation'
                AND expired.is_expired = 1
                AND expired.from_date >= '{filters.from_date}'
                AND expired.from_date <= '{filters.to_date}'
            ), 0) as leaves_expired
        FROM 
            `tabEmployee` e,
            `tabLeave Type` lt
        WHERE 
            e.status = 'Active' {employee_condition} {status_condition}
        ORDER BY 
            lt.name, e.employee_name
    """
    
    data = frappe.db.sql(query, as_dict=True)
    
    # Calculate closing balance and format data
    precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))
    for row in data:
        row.opening_balance = flt(row.opening_balance, precision)
        row.leaves_allocated = flt(row.leaves_allocated, precision)
        row.leaves_taken = flt(row.leaves_taken, precision)
        row.leaves_expired = flt(row.leaves_expired, precision)
        row.closing_balance = flt(
            row.opening_balance + row.leaves_allocated - row.leaves_taken - row.leaves_expired, 
            precision
        )
        row.indent = 1
    
    print(" Result is : ",data)
    return data

def get_chart_data(data, filters):
    if not data or not filters.get("employee"):
        return None
    
    labels = []
    datasets = []
    
    # Prepare data for chart
    leave_data = {}
    for row in data:
        if row.leave_type not in leave_data:
            leave_data[row.leave_type] = []
        leave_data[row.leave_type].append(row.closing_balance)
    
    # Create chart dataset
    for leave_type, balances in leave_data.items():
        datasets.append({
            "name": leave_type,
            "values": balances
        })
        labels.append(leave_type)
    
    return {
        "data": {
            "labels": labels,
            "datasets": datasets
        },
        "type": "bar",
        "colors": ["#456789", "#EE8888", "#7E77BF"],
    }
