import frappe

# Employee Checkin "Location / Device ID" value that marks a checkin as made
# from the office/local device. When set, the checkin's own "Purpose" field
# (custom_purpose: "In Office" / "Out Office") tells us whether that specific
# IN or OUT log counts as IO or OO. Historical checkins recorded before the
# Purpose field existed have it blank, so we fall back to the log_type itself
# (IN -> In Office/IO, OUT -> Out Office/OO) in that case.
LOCAL_DEVICE_ID = "set_local"

PURPOSE_TO_TAG = {
    "In Office": "IO",
    "Out Office": "OO",
}

LOG_TYPE_FALLBACK_TAG = {
    "IN": "IO",
    "OUT": "OO",
}


def get_local_checkin_tags(employee_ids, start_date, end_date):
    """Returns {(employee, date): {"IN": tag_or_None, "OUT": tag_or_None}} for
    checkins made on the local device. Looked up directly from Employee
    Checkin so it works both for the current day (live checkins) and for past
    months already rolled up into Attendance."""
    employee_ids = [e for e in (employee_ids or []) if e]
    if not employee_ids:
        return {}

    rows = frappe.db.sql(
        """
        SELECT employee, DATE(time) AS checkin_date, log_type, custom_purpose
        FROM `tabEmployee Checkin`
        WHERE employee IN %(employees)s
          AND DATE(time) BETWEEN %(start_date)s AND %(end_date)s
          AND device_id = %(device_id)s
        """,
        {
            "employees": tuple(employee_ids),
            "start_date": start_date,
            "end_date": end_date,
            "device_id": LOCAL_DEVICE_ID,
        },
        as_dict=True,
    )

    tags = {}
    for row in rows:
        if row.log_type not in ("IN", "OUT"):
            continue
        purpose = (row.custom_purpose or "").strip()
        tag = PURPOSE_TO_TAG.get(purpose) or LOG_TYPE_FALLBACK_TAG[row.log_type]
        key = (row.employee, row.checkin_date)
        tags.setdefault(key, {"IN": None, "OUT": None})[row.log_type] = tag
    return tags


def local_tag(tags, employee, date, log_type):
    """Returns the "IO"/"OO" tag for that employee's checkin of the given
    log_type on that date if it was made on the local device, else None."""
    entry = tags.get((employee, date))
    if not entry:
        return None
    return entry.get(log_type)
