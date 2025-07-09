from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, format_date, getdate, nowdate
from datetime import datetime, timedelta
from erpnext.setup.doctype.employee.employee import Employee
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from hrms.hr.doctype.leave_application.leave_application import LeaveApplication


class CustomLeaveDayAndDateValidation(LeaveApplication):
    def before_save(self):
        self.run_validations()
        
    def validate(self):
        self.run_validations()
    
    def before_submit(self):
        self.run_validations()
    
    def run_validations(self):
        """Centralized validation method called from all hooks"""
        filters = [
            ["employee", "=", self.employee],
            ["docstatus", "<", 2],  # Draft(0) or Submitted(1) documents
            ["status", "!=", "Rejected"],  # Ignore rejected leaves
            ["from_date", "<=", self.to_date],
            ["to_date", ">=", self.from_date]
         ]
    
        # Exclude current document if it's being updated
        if self.name:
            filters.append(["name", "!=", self.name])
        
        existing_leaves = frappe.get_all(
            "Leave Application",
            filters=filters,
            fields=["name", "from_date", "to_date", "leave_type", "status"]
        )
        
        if existing_leaves:
            # Prepare details of conflicting leaves
            conflict_details = []
            for leave in existing_leaves:
                conflict_details.append(
                    _("({0} to {1})").format(
                        format_date(leave.from_date),
                        format_date(leave.to_date)
                    )
                )
            
            frappe.throw(
                _("You've already applied for leave during the following dates: {0}").format(
                    "<br>".join(conflict_details),
                ),
                title=_("Leave Date Overlaps")
            )
            
        aleart_doc = frappe.get_doc("ArcHR Settings")
        
        if aleart_doc.enabled_day_validation_annual_leave == 1:
            self.validate_annual_leave_balance()

        if aleart_doc.enabled_date_validation == 1:
            self.validate_posting_date_range()
            
        # Ensure total_leave_days is calculated properly
        if not self.total_leave_days or self.total_leave_days == 0:
            self.total_leave_days = self.calculate_leave_days()
            

    def validate_posting_date_range(self):
        if not self.posting_date:
            return

        posting_date = getdate(self.posting_date)
        current_date = posting_date
        current_month = current_date.month
        current_year = current_date.year

        if current_month == 1:
            last_month_year = current_year - 1
            last_month = 12
        else:
            last_month_year = current_year
            last_month = current_month - 1

        last_month_name = datetime(last_month_year, last_month, 1).strftime('%B')
        current_month_name = datetime(current_year, current_month, 1).strftime('%B')

        if not self.from_date:
            return
            
        from_date = getdate(self.from_date)

        if from_date > posting_date:
            return

        if 1 <= posting_date.day <= 25:
            range_start = datetime(last_month_year, last_month, 21).date()
            
            if from_date < range_start:
                frappe.throw(
                    _('The maximum "From Date" <b>21st {0} {1}</b> is allowed.').format(
                        last_month_name, last_month_year
                    )
                )

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

        leave_details = self.get_leave_allocation_details()
        if not leave_details:
            frappe.throw(_("Could not fetch leave allocation details."))
            return

        current_year = datetime.now().year
        existing_leaves = self.get_existing_leaves(current_year)

        new_leave_days = self.calculate_leave_days()
        if new_leave_days is None:
            return

        total_used_leaves = sum(leave["total_leave_days"] for leave in existing_leaves)
        
        total_after_new = total_used_leaves + new_leave_days
        if total_after_new > leave_details and self.leave_type == "Annual Leave":
            frappe.throw(_(
                "<b>Total of the leave days exceeds your current allowance.</b> "
                "Please reduce the number of days or select a different leave type."
            ))

    
    
    def get_leave_allocation_details(self):
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
        return frappe.get_all("Leave Application",
            filters=[
                ["employee", "=", self.employee],
                ["leave_type", "=", "Annual Leave"],
                ["from_date", ">=", f"{year}-01-01"],
                ["from_date", "<=", f"{year}-12-31"],
                ["status", "in", ["Open", "Approved"]],
                ["name", "!=", self.name]
            ],
            fields=["total_leave_days"]
        )

    def calculate_leave_days(self):
        """Calculate the number of leave days in the current application"""
        if not self.from_date or not self.to_date:
            return 0
            
        try:
            from_date = getdate(self.from_date)
            to_date = getdate(self.to_date)
            
            if from_date > to_date:
                if frappe.get_doc("ArcHR Settings").zero_days_validation:
                    frappe.throw(_("From date cannot be after To date"))
                return 0
            
            # Get leave type settings
            leave_type = frappe.get_doc("Leave Type", self.leave_type)
            include_holidays = leave_type.include_holiday
            zero_days_validation = frappe.get_doc("ArcHR Settings").zero_days_validation

            if include_holidays:
                # Simple date difference if holidays are included
                total_days = (to_date - from_date).days + 1
                if zero_days_validation and total_days <= 0:
                    frappe.throw(_("Leave days cannot be zero or negative."))
                return total_days
            else:
                # Calculate working days excluding holidays and weekends
                working_days = self.calculate_working_days(from_date, to_date)
                if zero_days_validation and working_days <= 0:
                    frappe.throw(_("Leave days cannot be zero or negative after excluding holidays and weekends."))
                return working_days

        except Exception as e:
            if frappe.get_doc("ArcHR Settings").zero_days_validation:
                frappe.throw(_(""))
            return 0

    def calculate_working_days(self, from_date, to_date):
        """Calculate working days between two dates excluding holidays and weekends"""
        from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday
        
        holiday_list = frappe.db.get_value("Employee", self.employee, "holiday_list")
        if not holiday_list:
            frappe.throw(_("Please set Holiday List for employee {0}").format(self.employee))
        
        working_days = 0
        current_date = from_date
        while current_date <= to_date:
            if not is_holiday(holiday_list, current_date):
                working_days += 1
            current_date += timedelta(days=1)
        return working_days
    
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