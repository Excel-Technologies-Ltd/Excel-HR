from frappe import _

def get_dashboard_data(data=None, **kwargs):
    # Keep this side-effect free; just return the dashboard config.
    return {
        # This must be the link field used by related docs (e.g., Attendance) to point to the current doc.
        # For Leave Application dashboards, "employee" is the correct field.
        "fieldname": "employee",

        "transactions": [
            {"items": ["Attendance"]},
        ],

        "reports": [
            {"label": _("Reports"), "items": ["Excel Employee Leave Balance"]},
        ],

        # Optional but harmless; makes the link field explicit for each target doctype
        "non_standard_fieldnames": {
            "Attendance": "employee",
        },
    }


# from frappe import _

# def get_dashboard_data(data=None, **kwargs):
#     # Return dummy data matching the template structure
#     return {
#         "Annual Leave": {
#             "total_leaves": 20,
#             "expired_leaves": 2,
#             "leaves_taken": 10,
#             "leaves_pending_approval": 3,
#             "remaining_leaves": 5
#         },
#         "Special Leave": {
#             "total_leaves": 20,
#             "expired_leaves": 2,
#             "leaves_taken": 10,
#             "leaves_pending_approval": 3,
#             "remaining_leaves": 5
#         },
#         "Sick Leave": {
#             "total_leaves": 10,
#             "expired_leaves": 0,
#             "leaves_taken": 4,
#             "leaves_pending_approval": 1,
#             "remaining_leaves": 5
#         },
#         "Casual Leave": {
#             "total_leaves": 12,
#             "expired_leaves": 1,
#             "leaves_taken": 8,
#             "leaves_pending_approval": 2,
#             "remaining_leaves": 1
#         },
#     }