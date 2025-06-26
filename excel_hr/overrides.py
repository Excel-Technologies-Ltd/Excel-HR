import frappe
from erpnext.setup.doctype.employee.employee import Employee
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, format_date
from datetime import datetime, timedelta
from frappe import _

class CustomLeaveApplication(Document):
    def validate(self):
        self.validate_posting_date_range()
        self.validate_annual_leave_balance()

    def validate_posting_date_range(self):
        if not self.posting_date:
            return

        posting_date = datetime.strptime(self.posting_date, "%Y-%m-%d").date()
        current_date = datetime.now().date()
        current_month = current_date.month
        current_year = current_date.year

        # Get month names
        last_month_date = datetime(current_year, current_month - 1, 1)
        last_month_name = last_month_date.strftime('%B')
        current_month_name = datetime(current_year, current_month, 1).strftime('%B')

        if posting_date.day >= 1 and posting_date.day <= 25:
            # Check if from_date is between last month's 21st and current month's 20th
            range_start = datetime(current_year, current_month - 1, 21).date()
            
            from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date() if self.from_date else None
            
            if from_date and from_date < range_start:
                if from_date > posting_date:
                    return
                frappe.throw(f'The maximum "From Date" <b>21st {last_month_name} {current_year}</b> is allowed.')
                
        elif posting_date.day >= 26 and posting_date.day <= 31:
            # Check if from_date is between current month's 21st and last day of month
            range_start = datetime(current_year, current_month, 21).date()
            last_day_of_month = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).date()
            
            from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date() if self.from_date else None
            
            if from_date and (from_date < range_start or from_date > last_day_of_month):
                frappe.throw(f'The maximum "From Date" <b>21st {current_month_name} {current_year}</b> is allowed.')

    def validate_annual_leave_balance(self):
        if not self.employee:
            frappe.throw('Please select an employee.')
            return

        # Get leave allocation details
        leave_details = frappe.get_doc("Leave Allocation", {
            "employee": self.employee,
            "leave_type": "Annual Leave",
            "docstatus": 1
        })

        if not leave_details:
            frappe.throw('Could not fetch leave allocation details.')
            return

        total_allocated_leaves = leave_details.total_leaves_allocated

        # Calculate new leave days
        from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()
        to_date = datetime.strptime(self.to_date, "%Y-%m-%d").date()
        new_leave_days = (to_date - from_date).days + 1

        # Get existing approved leaves for the year
        current_year = datetime.now().year
        existing_leaves = frappe.get_all("Leave Application",
            filters=[
                ["employee", "=", self.employee],
                ["leave_type", "=", "Annual Leave"],
                ["from_date", ">=", f"{current_year}-01-01"],
                ["from_date", "<=", f"{current_year}-12-31"],
                ["status", "in", ["Open", "Approved"]]
            ],
            fields=["from_date", "to_date", "total_leave_days"]
        )

        total_used_leaves = sum(leave.total_leave_days for leave in existing_leaves)
        total_after_new = total_used_leaves + new_leave_days

        if total_after_new > total_allocated_leaves:
            frappe.throw('<b>Total of the leave days exceeds your current allowance.</b> Please reduce the number of days or select a different leave type.')


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
