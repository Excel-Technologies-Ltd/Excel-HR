import frappe
from erpnext.setup.doctype.employee.employee import Employee
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, format_date
from datetime import datetime, timedelta
from frappe import _

class EnabledDayValidation(LeaveApplication):
    
    def validate(self):
        aleart_doc=frappe.get_doc("ArcHR Settings")
        if aleart_doc.enabled_day_validation_annual_leave == 1:
            self.validate_annual_leave_balance()
        
    def validate_annual_leave_balance(self):
        if not self.employee:
            frappe.throw(_("Please select an employee."))
            return

        # Step 1: Fetch the annual leave allocation for the employee
        leave_details = self.get_leave_allocation_details()
        if not leave_details:
            frappe.throw(_("Could not fetch leave allocation details."))
            return

        # Step 2: Query previous leave applications within the same year
        current_year = datetime.now().year
        existing_leaves = self.get_existing_leaves(current_year)

        # Calculate new leave days
        new_leave_days = self.calculate_leave_days()
        if new_leave_days is None:
            return

        # Step 3: Sum the leave days from previous applications
        total_used_leaves = sum(leave["total_leave_days"] for leave in existing_leaves)
        
        # Step 4: Check if the total exceeds the allocated annual leave
        total_after_new = total_used_leaves + new_leave_days
        if total_after_new > leave_details:
            frappe.throw(_(
                "<b>Total of the leave days exceeds your current allowance.</b> "
                "Please reduce the number of days or select a different leave type."
            ))

    def get_leave_allocation_details(self):
        """Get the total allocated annual leaves for the employee"""
        try:
            leave_details = frappe.get_doc("Leave Allocation", {
                "employee": self.employee,
                "leave_type": "Annual Leave",
                "docstatus": 1
            })
            return leave_details.total_leaves_allocated
        except Exception:
            return None

    def get_existing_leaves(self, year):
        """Get all approved/annual leaves for the employee in the given year"""
        return frappe.get_all("Leave Application",
            filters=[
                ["employee", "=", self.employee],
                ["leave_type", "=", "Annual Leave"],
                ["from_date", ">=", f"{year}-01-01"],
                ["from_date", "<=", f"{year}-12-31"],
                ["status", "in", ["Open", "Approved"]],
                ["name", "!=", self.name]  # Exclude current document if updating
            ],
            fields=["total_leave_days"]
        )

    def calculate_leave_days(self):
        """Calculate the number of leave days in the current application"""
        if not self.from_date or not self.to_date:
            return None
            
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d").date()
        return (to_date - from_date).days + 1
    

class EnabledDateValidation(LeaveApplication):
    def validate(self):
        aleart_doc=frappe.get_doc("ArcHR Settings")
        if aleart_doc.enabled_date_validation == 1:
            self.validate_posting_date_range()

    def validate_posting_date_range(self):
        if not self.posting_date:
            return

        # Convert string dates to datetime objects
        posting_date = datetime.strptime(self.posting_date, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        current_month = current_date.month  # Current month (1-12)
        current_year = current_date.year

        # Get month names
        last_month_date = datetime(current_year, current_month - 1, 1)
        last_month_name = last_month_date.strftime('%B')  # Full month name

        current_month_name = datetime(current_year, current_month, 1).strftime('%B')

        if not self.from_date:
            return
            
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()

        # Check if posting date is between 1st and 25th of the current month
        if posting_date.day >= 1 and posting_date.day <= 25:
            # Set from_date range to last month's 21st to current month's 20th
            range_start = datetime(current_year, current_month - 1, 21).date()  # 21st of last month
            range_end = datetime(current_year, current_month, 25).date()  # 25th of current month

            # Skip validation if from_date is after posting_date
            if from_date > posting_date:
                return

            if from_date < range_start:
                frappe.throw(
                    _('The maximum "From Date" <b>21st {0} {1}</b> is allowed.').format(
                        last_month_name, current_year
                    )
                )

        # Check if posting date is between 26th and 31st of the current month
        elif posting_date.day >= 26 and posting_date.day <= 31:
            # Set from_date range to 21st of current month to last day of month
            range_start = datetime(current_year, current_month, 21).date()
            last_day_of_month = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).date()

            if from_date < range_start or from_date > last_day_of_month:
                frappe.throw(
                    _('The maximum "From Date" <b>21st {0} {1}</b> is allowed.').format(
                        current_month_name, current_year
                    )
                )

class CustomAttendanceRequest(AttendanceRequest):
    def before_save(self):
        aleart_doc=frappe.get_doc("ArcHR Settings")
        if aleart_doc.validate_future_date_in_attendance_request == 1:
            if getdate(self.from_date) > getdate(nowdate()):
                frappe.throw(_("You cannot create an attendance request for future dates."))
    def validate_dates(self):
        date_of_joining, relieving_date = frappe.db.get_value(
            "Employee", self.employee, ["date_of_joining", "relieving_date"]
        )
        
        if getdate(self.from_date) > getdate(self.to_date):
            frappe.throw(_("To date cannot be less than from date"))
        elif getdate(self.from_date) > getdate(nowdate()):
            # Changed from throw to msgprint for future dates
            frappe.msgprint(
                _("Creating attendance request for future dates: {0} to {1}").format(
                    frappe.bold(format_date(self.from_date)),
                    frappe.bold(format_date(self.to_date))
                ),
                indicator="orange",
                alert=True
            )
        elif date_of_joining and getdate(self.from_date) < getdate(date_of_joining):
            frappe.throw(_("From date cannot be less than employee's joining date"))
        elif relieving_date and getdate(self.to_date) > getdate(relieving_date):
            frappe.throw(_("To date cannot be greater than employee's relieving date"))


class UserWithEmployee(Employee):
    def before_save(self):
        user_company_mail = self.get("company_email")
        employee_number = self.get("employee_number")
        self.name = employee_number
        user_id = self.get("user_id")

        if not user_company_mail and employee_number:
            lowercase_employee_number = employee_number.lower()
            user_company_mail = f"{lowercase_employee_number}@excelbd.com"

        user = frappe.db.exists("User", user_company_mail)

        if user:
            self.company_email = user_id
            return

        if not user and user_id:
            self.company_email = user_id
            return

        # Creating a new User document
        new_user = frappe.get_doc(
            {
                "doctype": "User",
                "email": user_company_mail,
                "first_name": self.get("first_name"),
                "middle_name": self.get("middle_name"),
                "last_name": self.get("last_name"),
                "full_name": " ".join(
                    filter(
                        None,
                        [
                            self.get("first_name"),
                            self.get("middle_name"),
                            self.get("last_name"),
                        ],
                    )
                ),
                "username": self.get("first_name").lower(),
                "mobile_no": self.get("excel_official_mobile_no"),
                # Set username as lowercase of the first name
            }
        )

        new_user.insert(ignore_permissions=True)

        # Set other relevant fields and save the Employee document
        self.company_email = user_company_mail
        self.user_id = user_company_mail
        self.create_user_permission = 1

        # Save the Employee document

        frappe.msgprint("User created successfully.")
