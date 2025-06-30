from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, format_date, getdate, nowdate
from datetime import datetime, timedelta
from erpnext.setup.doctype.employee.employee import Employee
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication


class EnabledDayValidation(LeaveApplication):
    def before_save(self):
        aleart_doc = frappe.get_doc("ArcHR Settings")
        if aleart_doc.enabled_day_validation_annual_leave == 1:
            self.validate_annual_leave_balance()

        aleart_doc = frappe.get_doc("ArcHR Settings")
        if aleart_doc.enabled_date_validation == 1:
            self.validate_posting_date_range()
    def validate(self):
        aleart_doc = frappe.get_doc("ArcHR Settings")
        print("Enabled Day Validation Annual Leave:", aleart_doc.enabled_day_validation_annual_leave)
        if aleart_doc.enabled_day_validation_annual_leave == 1:
            self.validate_annual_leave_balance()
        aleart_doc = frappe.get_doc("ArcHR Settings")
        if aleart_doc.enabled_date_validation == 1:
            self.validate_posting_date_range()    
    def before_submit(self):
        aleart_doc = frappe.get_doc("ArcHR Settings")
        print("Enabled Day Validation Annual Leave:", aleart_doc.enabled_day_validation_annual_leave)
        if aleart_doc.enabled_day_validation_annual_leave == 1:
            self.validate_annual_leave_balance()  
        aleart_doc = frappe.get_doc("ArcHR Settings")
        if aleart_doc.enabled_date_validation == 1:
            self.validate_posting_date_range()      
    
    def validate_posting_date_range(self):
        if not self.posting_date:
            return

        # Use getdate() which handles both strings and date objects
        posting_date = getdate(self.posting_date)
        current_date = getdate()
        current_month = current_date.month  # Current month (1-12)
        current_year = current_date.year

        # Handle month/year rollover for January
        if current_month == 1:
            last_month_year = current_year - 1
            last_month = 12
        else:
            last_month_year = current_year
            last_month = current_month - 1

        # Get month names
        last_month_name = datetime(last_month_year, last_month, 1).strftime('%B')  # Full month name
        current_month_name = datetime(current_year, current_month, 1).strftime('%B')

        if not self.from_date:
            return
            
        from_date = getdate(self.from_date)

        # Skip validation if from_date is after posting_date
        if from_date > posting_date:
            return

        # Check if posting date is between 1st and 25th of current month
        if 1 <= posting_date.day <= 25:
            range_start = datetime(last_month_year, last_month, 21).date()
            
            if from_date < range_start:
                frappe.throw(
                    _('The maximum "From Date" <b>21st {0} {1}</b> is allowed.').format(
                        last_month_name, last_month_year
                    )
                )

        # Check if posting date is between 26th and 31st of current month
        elif 26 <= posting_date.day <= 31:
            range_start = datetime(current_year, current_month, 21).date()
            last_day_of_month = (datetime(current_year, current_month + 1, 1) - timedelta(days=1)).date()

            if from_date < range_start or from_date > last_day_of_month:
                frappe.throw(
                    _('The maximum "From Date" <b>21st {0} {1}</b> is allowed.').format(
                        current_month_name, current_year
                    )
                )


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
        if total_after_new > leave_details and self.leave_type == "Annual Leave":
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
            
        if isinstance(self.from_date, str):
            from_date = datetime.strptime(self.from_date, "%Y-%m-%d").date()
        else:
            from_date = self.from_date
            
        if isinstance(self.to_date, str):
            to_date = datetime.strptime(self.to_date, "%Y-%m-%d").date()
        else:
            to_date = self.to_date
            
        return (to_date - from_date).days + 1
    

class EnabledDateValidation(LeaveApplication):
    print("\n\n\n\n")
    print("Enabled Date Validation Leave Application")

    print("\n\n\n\n")
    # def before_save(self):
    #     aleart_doc = frappe.get_doc("ArcHR Settings")
    #     print("Enabled Date Validation Leave Application:", aleart_doc.enabled_date_validation)
    #     if aleart_doc.enabled_date_validation == 1:
    #         self.validate_posting_date_range()    
    # def validate(self):
    #     aleart_doc = frappe.get_doc("ArcHR Settings")
    #     if aleart_doc.enabled_date_validation == 1:
    #         self.validate_posting_date_range()
    # def before_submit(self):
    #     aleart_doc = frappe.get_doc("ArcHR Settings")
    #     if aleart_doc.enabled_date_validation == 1:
    #         self.validate_posting_date_range()        

    


class CustomAttendanceRequest(AttendanceRequest):
    def should_mark_attendance(self, attendance_date: str) -> bool:
        # Only check for leave records, skip holiday check
        if self.has_leave_record(attendance_date):
            frappe.msgprint(
                _("Attendance not submitted for {0} as {1} is on leave.").format(
                    frappe.bold(format_date(attendance_date)), frappe.bold(self.employee)
                )
            )
            return False
        return True

    @frappe.whitelist()
    def get_attendance_warnings(self) -> list:
        attendance_warnings = []
        request_days = date_diff(self.to_date, self.from_date) + 1

        for day in range(request_days):
            attendance_date = add_days(self.from_date, day)

            if self.has_leave_record(attendance_date):
                attendance_warnings.append({"date": attendance_date, "reason": "On Leave", "action": "Skip"})
            else:
                attendance = self.get_attendance_record(attendance_date)
                if attendance:
                    attendance_warnings.append(
                        {
                            "date": attendance_date,
                            "reason": "Attendance already marked",
                            "record": attendance,
                            "action": "Overwrite",
                        }
                    )

        return attendance_warnings

    def before_save(self):
        alert_doc = frappe.get_doc("ArcHR Settings")
        if alert_doc.validate_future_date_in_attendance_request == 1:
            if getdate(self.from_date) > getdate(nowdate()):
                frappe.throw(_("You cannot create an attendance request for future dates."))
    def before_submit(self):
        alert_doc = frappe.get_doc("ArcHR Settings")
        if alert_doc.validate_future_date_in_attendance_request == 1:
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