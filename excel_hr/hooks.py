from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "excel_hr"
app_title = "Excel Hr"
app_publisher = "Shaid Azmin"
app_description = "Excel Technologies HR Solutions "
app_email = "azmin@excelbd.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/excel_hr/css/excel_hr.css"
# app_include_js = "/assets/excel_hr/js/excel_hr.js"

# include js, css files in header of web template
# web_include_css = "/assets/excel_hr/css/excel_hr.css"
# web_include_js = "/assets/excel_hr/js/excel_hr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "excel_hr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# fixtures = ["Custom Field"]
# override_doctype_dashboards = {
# "Task": "custom_field_prefixing.task.get_dashboard_data"
# }
fixtures = ["Print Format", "Custom Field", "Property Setter", "Client Script",]
#     {
#         "dt": "Custom Field",
#         "filters": [
#             [
#                 "name",
#                 "in",
#                 [
#                     "Leave Application-custom_test_fixtures",
#                     "Leave Application-custom_head_of_department",
#                     "Leave Application-custom_line_manager_two",
#                     "Leave Application-custom_line_manager_one",
#                     "Leave Application-custom_approver_remarks",
#                     "Leave Application-workflow_state",
#                     "Leave Application-custom_head_of_dept_name",
#                     "Leave Application-custom_line_manager_two_name",
#                     "Leave Application-custom_line_manager_one_name",
#                     "Leave Application-custom_employee_image",
#                     "Leave Application-custom_branch",
#                     "Leave Application-custom_designation",
#                     "Leave Application-custom_branch",
#                     "Leave Application-custom_designation",
#                     "Leave Application-custom_employee_mobile_no",
#                     "Leave Application-custom_employee_email"
#                 ],
#             ],
#         ]
#     },
# ]

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# "methods": "excel_hr.utils.jinja_methods",
# "filters": "excel_hr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "excel_hr.install.before_install"
# after_install = "excel_hr.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "excel_hr.uninstall.before_uninstall"
# after_uninstall = "excel_hr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "excel_hr.utils.before_app_install"
# after_app_install = "excel_hr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "excel_hr.utils.before_app_uninstall"
# after_app_uninstall = "excel_hr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "excel_hr.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes
patches = [
    "custom_hr.patches.add_allow_future_attendance_field"
]

override_doctype_class = {
    "Employee": "excel_hr.overrides.UserWithEmployee",
    "Attendance Request": "excel_hr.attendance_request.NewAttendanceRequest",
}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#     "Employee": {
#         "on_create": "excel_hr.create_user_by_employee.create_user_by_employee",
#         "on_update": "excel_hr.create_user_by_employee.create_user_by_employee",
#     },
#     "User": {
#         "on_update": "excel_hr.create_user_by_employee.rename_employee_mail",
#         # "on_update": "excel_hr.create_user_by_employee.create_user_by_employee",
#     }

# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    "cron": {
        "*/2 * * * *": [
            "erpnext.stock.doctype.repost_item_valuation.repost_item_valuation.repost_entries",
        ],
        "0 7 * * *": [
            "excel_hr.reminders.send_absent_alert_for_missing_attendance",
        ],
    },
    "daily": [
		"excel_hr.reminders.send_birthday_reminders",
		"excel_hr.reminders.send_work_anniversary_reminders"
	],
    # "all": [
    #     "excel_hr.tasks.all"
    # ],
    # "daily": [
    #     "excel_hr.tasks.daily"
    # ],
    # "hourly": [
    #     "excel_hr.tasks.hourly"
    # ],
    # "weekly": [
    #     "excel_hr.tasks.weekly"
    # ],
    # "monthly": [
    #     "excel_hr.tasks.monthly"
    # ],
}

# Testing
# -------

# before_tests = "excel_hr.install.before_tests"

# Overriding Methods
# ------------------------------
#

# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# "Task": "excel_hr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["excel_hr.utils.before_request"]
# after_request = ["excel_hr.utils.after_request"]

# Job Events
# ----------
# before_job = ["excel_hr.utils.before_job"]
# after_job = ["excel_hr.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# {
# "doctype": "{doctype_1}",
# "filter_by": "{filter_by}",
# "redact_fields": ["{field_1}", "{field_2}"],
# "partial": 1,
# },
# {
# "doctype": "{doctype_2}",
# "filter_by": "{filter_by}",
# "partial": 1,
# },
# {
# "doctype": "{doctype_3}",
# "strict": False,
# },
# {
# "doctype": "{doctype_4}"
# }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# "excel_hr.auth.validate"
# ]
