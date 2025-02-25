from erpnext.setup.doctype.employee.employee import get_all_employee_emails, get_employee_email
import frappe
from frappe import _
from frappe.utils import add_days, add_months, comma_sep, getdate, today
from hrms.controllers.employee_reminders import get_sender_email,get_employees_who_are_born_today,get_employees_having_an_event_today 


from frappe.core.doctype.sms_settings.sms_settings import send_sms 
from excel_hr.api import send_anniversary_wish,send_birthday_wish


def send_birthday_reminders():
    """Send Employee birthday reminders if no 'Stop Birthday Reminders' is not set."""
    to_send = int(frappe.db.get_single_value("Excel Alert Settings", "birthday_reminder"))
    if not to_send:
        return
    
    sender = get_sender_email()
    employees_born_today = get_employees_who_are_born_today()
    
    for company, birthday_persons in employees_born_today.items():
        for person in birthday_persons:
            company_email = get_company_email(person.user_id)
            full_name = get_employee_full_name(person.user_id)
            send_birthday_wish(company_email,full_name)
            
           
       
      
        
        
        
def send_work_anniversary_reminders():
    """Send Employee work anniversary reminders if no 'Stop Work Anniversary Reminders' is not set."""
    to_send = int(frappe.db.get_single_value("Excel Alert Settings", "anniversary_reminder"))
    if not to_send:
        return
    sender = get_sender_email()
    employees_joined_today = get_employees_having_an_event_today("work_anniversary")
    print(employees_joined_today.items())
    for company, anniversary_persons in employees_joined_today.items():
        for person in anniversary_persons:
            company_email = get_company_email(person.user_id)
            full_name = get_employee_full_name(person.user_id)
            send_anniversary_wish(company_email,full_name)
        
    
    
    
    
def get_company_email(userid):
    Employee = frappe.get_doc("Employee", {"user_id": userid})
    company_email= Employee.company_email
    if not company_email or company_email.startswith("etl") or company_email.startswith("eisl"):
        return Employee.leave_approver if Employee.leave_approver else Employee.personal_email
    else:
        return company_email
    
    
def get_employee_full_name(userid):
    Employee = frappe.get_doc("Employee", {"user_id": userid})
    return f"{Employee.employee_name}"
    
    
    
    

    