import frappe

# Employee Checkin "Location / Device ID" values that count as the office/local
# device. A checkin's IN log recorded on one of these is "In Office" (IO); an
# OUT log recorded on one of these is "Out Office" (OO). Everything else is
# treated as a remote/off-site checkin and gets no suffix.
LOCAL_DEVICE_IDS = ("HRT Flap Barrier-IN", "HRT Flap Barrier-OUT")


def get_local_checkin_tags(employee_ids, start_date, end_date):
    """Returns {(employee, date): {"IN": bool, "OUT": bool}} indicating, for each
    employee/date, whether their IN and/or OUT checkin was recorded on a local
    (office) device. Looked up directly from Employee Checkin so it works both
    for the current day (live checkins) and for past months already rolled up
    into Attendance."""
    employee_ids = [e for e in (employee_ids or []) if e]
    if not employee_ids:
        return {}

    rows = frappe.db.sql(
        """
        SELECT employee, DATE(time) AS checkin_date, log_type
        FROM `tabEmployee Checkin`
        WHERE employee IN %(employees)s
          AND DATE(time) BETWEEN %(start_date)s AND %(end_date)s
          AND device_id IN %(local_devices)s
        """,
        {
            "employees": tuple(employee_ids),
            "start_date": start_date,
            "end_date": end_date,
            "local_devices": LOCAL_DEVICE_IDS,
        },
        as_dict=True,
    )

    tags = {}
    for row in rows:
        if row.log_type not in ("IN", "OUT"):
            continue
        key = (row.employee, row.checkin_date)
        tags.setdefault(key, {"IN": False, "OUT": False})[row.log_type] = True
    return tags


def local_tag(tags, employee, date, log_type):
    """Returns "IO" / "OO" if that employee's checkin of the given log_type on
    that date was recorded on a local device, else None."""
    entry = tags.get((employee, date))
    if not entry:
        return None
    if log_type == "IN" and entry.get("IN"):
        return "IO"
    if log_type == "OUT" and entry.get("OUT"):
        return "OO"
    return None
