import frappe
import random
import string
# from frappe.permissions import (
#     add_user_permission,
#     get_doc_permissions,
#     has_permission,
#     remove_user_permission,
# )

def create_user_by_employee(doc, method=None):
    user_company_mail = doc.get('company_email')
    employee_number = doc.get('employee_number')
    user_id=doc.get('user_id')

    if not user_company_mail and employee_number:
        lowercase_employee_number = employee_number.lower()
        user_company_mail = f"{lowercase_employee_number}@excelbd.com"
    user = frappe.db.exists("User", user_company_mail)
    if user :
        return
    if user is None and user_id is not None:
        # take previouse user 
        # frappe.db.set_value('User', user_id, 'name', user_company_mail)
        # frappe.msgprint("work")
        return
    # Creating a new User document
    new_user = frappe.get_doc({
        "doctype": "User",
        "email": user_company_mail,
        "first_name": doc.get('first_name'),
        "middle_name": doc.get('middle_name'),
        "last_name": doc.get('last_name'),
        "full_name": " ".join(filter(None, [doc.get('first_name'), doc.get('middle_name'), doc.get('last_name')])),
        "username": doc.get('first_name').lower(),
        # Set username as lowercase of the first name
    })

    new_user.insert(ignore_permissions=True)
    doc.company_email=user_company_mail
    # doc.user_id=user_company_mail
    # doc.create_user_permission=1
    frappe.db.set_value(doc.doctype, doc.name, 'email', user_company_mail)
    frappe.msgprint('user_created')
    
    
def rename_employee_mail(doc, method=None):
    name = doc.name
    frappe.publish_realtime('employee_email', {"employee_email": name})

        

# def generate_strong_password(first_name):
#     # Set of special characters
#     special_characters = "!@#$%^&*()_-+=<>?/{}[]"

#     # Add the first name to the password``
#     password = first_name

#     # Add a random special character to the password
#     password += random.choice(special_characters)

#     # Add random alphanumeric characters to the password
#     for _ in range(6):  # You can adjust the number of alphanumeric characters based on your requirements
#         password += random.choice(string.ascii_letters + string.digits)

#     return password

# def update_email(doc, method=None):
#     existing_company_mail = frappe.db.get_value(doc.doctype, doc.name, 'company_email')
#     new_company_mail = doc.get('company_email') 
#     frappe.db.set_value("User", existing_company_mail, 'email', new_company_mail)
#     frappe.db.set_value(doc.doctype, doc.name, 'user_id', new_company_mail)
#     frappe.db.commit()
#     frappe.msgprint("Company email changed with user mail")

# def update_user_permissions(doc, method=None):
#     if not doc.create_user_permission:
#         return
#     if not has_permission("User Permission", ptype="write", raise_exception=False):
#         return

#     employee_user_permission_exists = frappe.db.exists(
#         "User Permission", {"allow": "Employee", "for_value": doc.name, "user": doc.user_id}
#     )

#     if not employee_user_permission_exists:
#         add_user_permission("Employee", doc.name, doc.user_id)
#         add_user_permission("Company", doc.company, doc.user_id)
