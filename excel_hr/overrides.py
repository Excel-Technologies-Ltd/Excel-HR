import frappe
from erpnext.setup.doctype.employee.employee import Employee

class UserWithEmployee(Employee):
    def before_save(self):
        user_company_mail = self.get('company_email')
        employee_number = self.get('employee_number')
        user_id = self.get('user_id')

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
        new_user = frappe.get_doc({
            "doctype": "User",
            "email": user_company_mail,
            "first_name": self.get('first_name'),
            "middle_name": self.get('middle_name'),
            "last_name": self.get('last_name'),
            "full_name": " ".join(filter(None, [self.get('first_name'), self.get('middle_name'), self.get('last_name')])),
            "username": self.get('first_name').lower(),
            "mobile_no":self.get('excel_official_mobile_no'),
            # Set username as lowercase of the first name
        })

        new_user.insert(ignore_permissions=True)

        # Set other relevant fields and save the Employee document
        self.company_email = user_company_mail
        self.user_id = user_company_mail
        self.create_user_permission = 1

        # Save the Employee document
        

        frappe.msgprint('User created successfully.')
