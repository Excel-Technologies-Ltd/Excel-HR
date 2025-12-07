from erpnext.setup.doctype.employee.employee import get_all_employee_emails, get_employee_email
import frappe
from frappe import _
from frappe.utils import add_days, add_months, comma_sep, getdate, today
from hrms.controllers.employee_reminders import get_employees_who_are_born_today,get_employees_having_an_event_today
from frappe.utils import getdate, add_days, formatdate


from frappe.core.doctype.sms_settings.sms_settings import send_sms

def send_absent_alert_for_missing_attendance():
    """Send email alerts to team leaders and employees who were absent yesterday."""
    
    try:
        # Check if absent reminders are enabled
        absent_reminder = int(frappe.db.get_single_value("ArcHR Settings", "absent_reminder"))
        if not absent_reminder:
            frappe.log("Absent reminder notifications are disabled in ArcHR Settings")
            return

        yesterday = add_days(getdate(), -1)
        yesterday_str = formatdate(yesterday)
        company = frappe.db.get_single_value("Global Defaults", "default_company") or "Excel Technologies Ltd."
        
        # Get all active employees
        employees = frappe.get_all('Employee', 
            filters={'status': 'Active'}, 
            fields=['name', 'employee_name', 'company_email', 'leave_approver', 'holiday_list', 'department']
        )
        
        if not employees:
            frappe.log("No active employees found")
            return
            
        absent_employees = {}
        total_absent = 0
        
        # Identify absent employees
        for emp in employees:
            if not emp.company_email:
                continue  # Skip employees without email

            # Check if yesterday was a holiday for this employee
            is_holiday = False
            # print(f"Checking holiday for {emp.employee_name} ({emp.holiday_list}) on {yesterday_str}")
            
            if emp.holiday_list:
                is_holiday = frappe.db.exists('Holiday', {
                    'parent': emp.holiday_list,
                    'holiday_date': yesterday
                })
                
            if is_holiday:
                # print(f"Employee {emp.employee_name} was on holiday on {yesterday_str}")
                continue  # Skip holiday    
            
            # Check attendance
            attendance_exists = frappe.db.exists('Attendance', {
                'employee': emp.name,
                'attendance_date': yesterday,
                'docstatus': 1
            })
            
            
            if not attendance_exists:
                approver = emp.leave_approver
                if approver:
                    if approver not in absent_employees:
                        absent_employees[approver] = []

                    absent_employees[approver].append({
                        'name': emp.employee_name,
                        'email': emp.company_email,
                        'department': emp.department 
                    })
                    total_absent += 1
                    # print(f"Employee {emp.employee_name} ({emp.name}) was absent on {yesterday_str}")
        
        frappe.log(f"Found {total_absent} absent employees for {yesterday_str}")
        
        if not absent_employees:
            return  # No absent employees
            
        # Send notifications
        for approver, employees_list in absent_employees.items():
            # Get approver details
            approver_details = frappe.get_value('Employee', {'company_email': approver}, 
                                            ['employee_name', 'company_email'], as_dict=True)
            
            if not approver_details or not approver_details.company_email:
                frappe.log(f"No valid email found for approver {approver}")
                continue
            
            # Send email to team leader using template
            email_args = {
                'yesterday_str': yesterday_str,
                'approver_name': approver_details.employee_name,
                'absent_employees': employees_list,
                'company': company
            }
            
            frappe.sendmail(
                recipients=[approver_details.company_email],
                subject=f"Absent Alert for your team members on {yesterday_str}",
                template="team_leader_absent_alert",
                args=email_args,
            )
            
            frappe.log(f"Sent absent alert to team leader {approver_details.employee_name}")
            
            # Send individual emails
            for emp in employees_list:
                if emp['email']:
                    email_args = {
                        'yesterday_str': yesterday_str,
                        'employee_name': emp['name'],
                        'company': company
                    }
                    
                    frappe.sendmail(
                        recipients=[emp['email']],
                        subject=f"Absent Alert for {yesterday_str}",
                        template="employee_absent_alert",
                        args=email_args
                    )
                    frappe.log(f"Sent absent alert to employee {emp['name']}")
        
    except Exception as e:
        frappe.log_error(f"Failed to send absent alerts: {str(e)}", "Absent Alert Error")
        frappe.throw("Failed to process absent alerts. Please check error logs.")

def warm_message():
    """A simple function to test scheduled tasks."""
    message = "Warm message from scheduled task executed successfully."
    print(message)

def send_birthday_reminders():
    """Send Employee birthday reminders if no 'Stop Birthday Reminders' is not set."""
    
    to_send = int(frappe.db.get_single_value("ArcHR Settings", "birthday_reminder"))
    if not to_send:
        print("Birthday reminders disabled in ArcHR Settings")
        frappe.logger().info("Birthday reminders disabled in ArcHR Settings")
        return

    employees_born_today = get_employees_who_are_born_today()

    print(f"\n\nEmployees born today: {dict(employees_born_today)}\n\n")
    send_all_birthday_mails(employees_born_today)

    
    
    # for company, birthday_persons in employees_born_today.items():
    #     for person in birthday_persons:  
    #         full_name = get_employee_full_name(person.user_id)
    #         location,department= get_job_location_and_department(person.user_id)
    #         if check_active_and_intern_employee(person.user_id):
    #             company_email = get_company_email(person.user_id)
    #             print("sending birthday wish to",company_email,full_name,department,location)
    #             send_birthday_wish(company_email,full_name,department,location)
    #         else:
    #             print(f"Employee {full_name} is not active or an intern")


def send_all_birthday_mails(employees):
    arc_hr_settings = frappe.get_doc("ArcHR Settings")
    email_id = frappe.db.get_value("Email Account", {"name": arc_hr_settings.birthday_sender_email}, "email_id")
    cc_mail = frappe.db.get_single_value("ArcHR Settings", "cc_mail")

    if cc_mail:
        cc_mail = cc_mail.split(",")
    else:
        cc_mail = None

    # Enrich employee data with department and location
    enriched_employees = {}
    for company, employee_list in employees.items():
        enriched_list = []
        for emp in employee_list:
            # Get additional employee details
            employee_doc = frappe.get_doc("Employee", {"user_id": emp.user_id})

            # Calculate age (optional - can be used for milestone birthdays)
            from datetime import datetime
            if hasattr(emp, 'date_of_birth') and emp.date_of_birth:
                age = datetime.today().year - emp.date_of_birth.year
            else:
                age = None

            # Create enriched employee object
            enriched_emp = {
                "name": emp.name,
                "image": emp.image,
                "department": employee_doc.excel_parent_department or employee_doc.department,
                "location": employee_doc.custom_job_location,
                "age": age,
                "user_id": emp.user_id,
                "years": ""  # Empty for birthday, used in template
            }
            enriched_list.append(enriched_emp)

        enriched_employees[company] = enriched_list

    frappe.sendmail(
        recipients="azmin@excelbd.com",
        subject=f"Happy Birthday to all Employees having birthday today",
        # cc=cc_mail,
        sender=email_id,
        template="birthday",
        args={
            "employees": enriched_employees,
            "today": getdate()
        },
        expose_recipients='header',
    )

    print(f"Birthday email sent successfully to azmin@excelbd.com")


def send_all_work_anniversary_mails(employees):
    arc_hr_settings = frappe.get_doc("ArcHR Settings")
    email_id = frappe.db.get_value("Email Account", {"name": arc_hr_settings.anniversary_sender_email}, "email_id")
    cc_mail = frappe.db.get_single_value("ArcHR Settings", "cc_mail")

    if cc_mail:
        cc_mail = cc_mail.split(",")
    else:
        cc_mail = None

    # Enrich employee data with department, location, and years
    enriched_employees = {}
    for company, employee_list in employees.items():
        enriched_list = []
        for emp in employee_list:
            # Get additional employee details
            employee_doc = frappe.get_doc("Employee", {"user_id": emp.user_id})

            # Calculate years of service
            years = count_anniversary_year(emp.date_of_joining)

            # Create enriched employee object
            enriched_emp = {
                "name": emp.name,
                "image": emp.image,
                "department": employee_doc.excel_parent_department or employee_doc.department,
                "location": employee_doc.custom_job_location,
                "years": years,
                "user_id": emp.user_id
            }
            enriched_list.append(enriched_emp)

        enriched_employees[company] = enriched_list

    frappe.sendmail(
        recipients="azmin@excelbd.com",
        subject=f"Happy Work Anniversary to all Employees having anniversary today",
        # cc=cc_mail,
        sender=email_id,
        template="work_anniversary",
        args={
            "employees": enriched_employees,
            "today": getdate()
        },
        expose_recipients='header',
    )

    print(f"Work anniversary email sent successfully to azmin@excelbd.com")


def send_work_anniversary_reminders():
    """Send Employee work anniversary reminders if no 'Stop Work Anniversary Reminders' is not set."""
    to_send = int(frappe.db.get_single_value("ArcHR Settings", "anniversary_reminder"))
    if not to_send:
        print("Work anniversary reminders disabled in ArcHR Settings")
        frappe.logger().info("Work anniversary reminders disabled in ArcHR Settings")
        return

    employees_joined_today = get_employees_having_an_event_today("work_anniversary")

    print(f"\n\nEmployees having work anniversary today: {dict(employees_joined_today)}\n\n")
    send_all_work_anniversary_mails(employees_joined_today)
        
    
    
    
    
def get_company_email(userid):
    Employee = frappe.get_doc("Employee", {"user_id": userid})
    company_email= Employee.company_email
    if company_email.startswith("etl") or company_email.startswith("eisl"):
        return Employee.leave_approver if Employee.leave_approver else Employee.personal_email
    else:
        return company_email
    
    
def get_employee_full_name(userid):
    try:
        employee = frappe.get_doc("Employee", {"user_id": userid})
        salutation = f"{employee.salutation}." if employee.salutation else ""
        full_name = f"{salutation} {employee.employee_name}".strip()
        return full_name
    except frappe.DoesNotExistError:
        return ""

    
def check_active_and_intern_employee(userid):
    employee = frappe.get_doc("Employee", {"user_id": userid})
    if employee.status != "Active":
        return False
    if not employee.company_email :
        return False
    
    if employee.employment_type == "Regular":
        return True
    
    if (employee.employment_type == "Contractual" and
        employee.custom_employment_sub_type == "Contractual"):
        return True
    
    return False

    
    

from datetime import datetime

def count_anniversary_year(joining_date):
    """Calculate the number of years since the employee joined."""
    today = datetime.today()
    years_difference = today.year - joining_date.year

    # Ensure years_difference is greater than 0 to apply the ordinal suffix
    if years_difference > 0:
        return f"{years_difference}{get_ordinal_suffix(years_difference)}"
    return "0"




def get_ordinal_suffix(n):
    """Return the ordinal suffix for a given number (1st, 2nd, 3rd, etc.)."""
    # Use only the last digit to determine the suffix
    last_digit = n % 10
    if last_digit == 1:
        return "st"
    elif last_digit == 2:
        return "nd"
    elif last_digit == 3:
        return "rd"
    else:
        return "th"
def get_job_location_and_department(id):
    employee= frappe.get_doc('Employee',{"user_id": id})
    return employee.custom_job_location,employee.excel_parent_department
