import frappe

@frappe.whitelist()
def get_holiday_list(parent):
    dynamic_parent = parent
    result = frappe.db.sql(
        """
        SELECT h.holiday_date
        FROM `tabHoliday` AS h
        WHERE h.parenttype='Holiday List' AND h.parent=%s
        """,
        (dynamic_parent,),
        as_dict=True
    )
    return result
