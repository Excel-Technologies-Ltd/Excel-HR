import frappe
from erpnext.setup.doctype.employee.employee import Employee
from hrms.hr.doctype.attendance_request.attendance_request import AttendanceRequest
from frappe.model.document import Document
from frappe.utils import getdate, nowdate, format_date
from frappe import _

class CustomAttendanceRequest(AttendanceRequest):
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
