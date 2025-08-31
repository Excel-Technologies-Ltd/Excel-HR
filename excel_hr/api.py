import frappe
from PIL import Image, ImageDraw, ImageFont
import io
import os
from frappe.utils import get_url,today
import frappe.utils
import requests
import base64
import random
from frappe import _
from hrms.controllers.employee_reminders import send_birthday_reminders
from datetime import datetime, timedelta
import math
import json
import re

@frappe.whitelist()
def get_departments_for_company(company):
    departments = frappe.db.sql_list("""
        SELECT DISTINCT department FROM `tabEmployee`
        WHERE company = %s AND department IS NOT NULL AND department != ''
        ORDER BY department
    """, company)
    return departments  # Returns list of strings




def get_employees_todays_checkin(employees):
    today_checkin = frappe.get_list(
        "Employee Checkin",
        fields=["*"],
        filters={"employee": ["in", employees], "time": ["between", [today() + " 00:00:00", today() + " 23:59:59"]]},
        order_by="time asc",
        ignore_permissions=False
    )
    return today_checkin

@frappe.whitelist()
def get_has_role(filters=None):
    roles_response = frappe.db.get_all(
        "Has Role",
        fields=["role", "parent"],
        filters= filters or {},
    ),
    if roles_response and isinstance(roles_response[0], list):
        roles = roles_response[0]
    else:
        roles = roles_response
    email_pattern = re.compile(r"[^@]+@[^@]+\.[^@]+")
    filtered = [r for r in roles if email_pattern.match(r.get("parent", ""))]
    return filtered
     


@frappe.whitelist()
def get_attendance_report_with_todays_checkin_and_checkout(
    filters=None,
    or_filters=None,
    order_by=None,
    limit_start=0,
    limit_page_length=20,
    fields=None
):
    from frappe.utils import today, getdate, date_diff, add_days
    import json

    filters = json.loads(filters) if isinstance(filters, str) else filters or []
    or_filters = json.loads(or_filters) if isinstance(or_filters, str) else or_filters or []
    fields = json.loads(fields) if isinstance(fields, str) else fields or ["*"]

    today_date = today()
    attendance_list = []

    # Extract date range
    from_date = to_date = today_date
    for f in filters:
        if f[0] == "attendance_date" and f[1] == "between":
            from_date, to_date = f[2][0], f[2][1]

    from_date = str(getdate(from_date))
    to_date = str(getdate(to_date))

    # Step 1: Get Attendance documents
    attendance_filters = [["attendance_date", "between", [from_date, to_date]]] + [f for f in filters if f[0] != "attendance_date"]
    existing_attendance = frappe.get_all(
        "Attendance",
        filters=attendance_filters,
        or_filters=or_filters,
        fields=["name", "employee", "attendance_date", "status"]
    )
    attendance_map = {(att["employee"], str(att["attendance_date"])): att for att in existing_attendance}

    # Step 2: Get check-ins for the full date range
    checkin_filters = [["time", "between", [from_date + " 00:00:00", to_date + " 23:59:59"]]]
    checkin_filters += [f for f in filters if f[0] != "attendance_date"]

    checkins = frappe.get_all(
        "Employee Checkin",
        fields=["*"],
        filters=checkin_filters,
        or_filters=or_filters,
        order_by="time asc",
        ignore_permissions=False
    )

    # Group check-ins by (employee, date)
    checkins_dict = {}
    for c in checkins:
        key = (c["employee"], str(getdate(c["time"])))
        checkins_dict.setdefault(key, []).append(c)

    # Step 3: Get filtered employee list
    # employee_filters = [f for f in filters if f[0] != "attendance_date"] { "status": "Active" }
    employee_filters = [f for f in filters if f[0] != "attendance_date"]
    employee_list = frappe.get_all("Employee", filters=employee_filters, or_filters=or_filters, fields=["name"])

    # Step 4: Build full attendance list
    num_days = date_diff(to_date, from_date) + 1
    for emp in employee_list:
        emp_id = emp["name"]
        for i in range(num_days):
            current_date = str(add_days(from_date, i))
            key = (emp_id, current_date)

            # Case 1: Document exists
            if key in attendance_map:
                att_doc = frappe.get_doc("Attendance", attendance_map[key]["name"])
                row = att_doc.as_dict()
                row["source"] = "Document"
                row["checkin_list"] = checkins_dict.get(key, [])[:1] + checkins_dict.get(key, [])[-1:]
            # Case 2: Check-in exists, but no document
            elif key in checkins_dict:
                checkins_for_day = checkins_dict[key]
                row = {
                    "employee": emp_id,
                    "full_name": frappe.get_value("Employee", emp_id, "employee_name"),
                    "department": frappe.get_value("Employee", emp_id, "department"),
                    "job_location": frappe.get_value("Employee", emp_id, "excel_job_location"),
                    "shift": frappe.get_value("Employee",emp_id, "default_shift"),
                    "attendance_date": current_date,
                    "status": "Present",
                    "source": "Checkin",
                    "checkin_list": [checkins_for_day[0], checkins_for_day[-1]]
                }
            # Case 3: No data at all
            else:
                continue
                # row = {
                #     "employee": emp_id,
                #     "full_name": frappe.get_value("Employee", emp_id, "employee_name"),
                #     "department": frappe.get_value("Employee", emp_id, "department"),
                #     "job_location": frappe.get_value("Employee", emp_id, "excel_job_location"),
                #     "shift": frappe.get_value("Employee",emp_id, "default_shift"),
                #     "attendance_date": current_date,
                #     "status": "Absent",
                #     "source": "Assumed",
                #     "checkin_list": []
                # }

            # Respect fields filter
            if fields == ["*"]:
                attendance_list.append(row)
            else:
                filtered_row = {k: row[k] for k in fields if k in row}
                attendance_list.append(filtered_row)

    # Step 5: Pagination
    paginated_result = attendance_list[int(limit_start):int(limit_start) + int(limit_page_length)]

    return paginated_result





@frappe.whitelist()
def get_holiday_list(parent):
    dynamic_parent = parent
    result = frappe.db.sql(
        """
        SELECT h.holiday_date
        FROM `tabHoliday` AS h
        WHERE h.parenttype='Holiday List' AND h.parent=%s
        """,
        (dynamic_parent,),
        as_dict=True
    )
    return result
@frappe.whitelist()
def generate_token(email):
    """
    Generate API key and secret for a user based on their email.

    Args:
        email (str): The email of the user (sent in the request body).

    Returns:
        dict: A dictionary containing the API key and secret.

    Raises:
        frappe.ValidationError: If the email is invalid or the user is disabled.
    """
    allowed_roles = ["System Manager"]  # Define allowed roles
    user_roles = frappe.get_roles(frappe.session.user)

    if not any(role in allowed_roles for role in user_roles):
        frappe.throw(
            "You are not authorized to access this resource", frappe.PermissionError
        )

    # Check if the user exists with the provided email
    user = frappe.db.get_value("User", {"email": email}, "name")
    if not user:
        frappe.throw("Invalid email")

    # Fetch the user document
    user_doc = frappe.get_doc("User", user)

    # Validate if the user is active
    if not user_doc.enabled:
        frappe.throw("User is disabled")

    # Generate API key and secret if not already generated
    if not user_doc.api_key:
        user_doc.api_key = frappe.generate_hash(length=15)
    if not user_doc.api_secret:
        user_doc.api_secret = frappe.generate_hash(length=15)
        user_doc.save(ignore_permissions=True)

    # Return the API key and secret
    return {
        "api_key": user_doc.api_key,
        "api_secret": user_doc.get_password("api_secret"),
    }










# final
def send_anniversary_wish(email="sohan.dev@excelbd.com", name="Mr. Sohanur Rahman Lelin Khan Mia", 
                         department="Engineering And Technology", job_location="Baridhara HR", 
                         anniversary_years="5th"):
    arc_hr_settings = frappe.get_doc("ArcHR Settings")
    cc_mail = frappe.db.get_single_value("ArcHR Settings", "cc_mail")
    
    
    birthday_image_path = "assets/excel_hr/ann.jpg"
    font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"

    if not os.path.exists(birthday_image_path):
        frappe.throw(f"File not found at {birthday_image_path}")
    if not os.path.exists(font_path):
        frappe.throw(f"Font file not found at {font_path}")

    image = Image.open(birthday_image_path)
    draw = ImageDraw.Draw(image)
    
    # Get image dimensions
    img_width, img_height = image.size

    # Font settings
    name_font_size = 20
    info_font_size = 16  # Smaller font size for info text
    anniversary_font_size = 14  # Font size for anniversary text
    years_font_size = 25  # Font size for "5 Year" text
    name_font = ImageFont.truetype(font_path, name_font_size)
    info_font = ImageFont.truetype(font_path, info_font_size)
    anniversary_font = ImageFont.truetype(font_path, anniversary_font_size)
    years_font = ImageFont.truetype(font_path, years_font_size)

    # Text content
    name_text = name
    info_text = f"{department}\n{job_location}"
    
    # Add "5 Year" text beside "Work" in "Happy Work Anniversary"
    years_text = anniversary_years
    
    # Calculate position relative to image dimensions
    # From the image, the red box appears to be roughly at:
    # - Horizontally: right after "Work" which is around 60% of the width
    # - Vertically: at about 35-40% from the top of the image
    years_x = int(img_width * 0.45)  # Position at approximately 60% of the image width
    years_y = int(img_height * 0.38)  # Position at approximately 38% of the image height
    
    # Draw the years text with orange color
    draw.text((years_x, years_y), years_text, fill="rgb(237, 125, 49)", font=years_font)
    
    # Calculate text dimensions for name and info
    try:
        # For name text
        name_bbox = draw.textbbox((0, 0), name_text, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_height = name_bbox[3] - name_bbox[1]
        
        # Calculate info text dimensions
        info_lines = info_text.split('\n')
        info_height = 0
        info_width = 0
        
        for line in info_lines:
            line_bbox = draw.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_height = line_bbox[3] - line_bbox[1]
            info_height += line_height
            info_width = max(info_width, line_width)
            
    except AttributeError:
        # Fallback for older Pillow versions
        name_width, name_height = name_font.getsize(name_text)
        
        info_lines = info_text.split('\n')
        info_height = 0
        info_width = 0
        
        for line in info_lines:
            line_width, line_height = info_font.getsize(line)
            info_height += line_height
            info_width = max(info_width, line_width)

    # Single box for both name and info text
    padding_h = 12  # Horizontal padding
    padding_v = 8  # Vertical padding
    line_spacing = 5  # Space between lines and between name and info
    
    # Calculate box width based on the wider of name or info
    box_width = max(name_width, info_width) + 2 * padding_h
    
    # Calculate box height to fit both name and info with spacing
    box_height = name_height + info_height + (len(info_lines) + 1) * line_spacing + 2 * padding_v
    
    # Position the box centrally
    box_x1 = (img_width - box_width) // 2
    box_y1 = img_height // 1.8  # Positioned midway down the image (adjust as needed)
    box_x2 = box_x1 + box_width
    box_y2 = box_y1 + box_height
    
    # Draw the box background
    draw.rectangle((box_x1, box_y1, box_x2, box_y2), fill="rgb(12, 46, 195)")
    
    # Draw name text (centered in the box)
    name_x = box_x1 + (box_width - name_width) // 2
    current_y = box_y1 + padding_v
    draw.text((name_x, current_y), name_text, fill="rgb(237, 125, 49)", font=name_font)
    
    # Update vertical position for info text (after name text)
    current_y += name_height + line_spacing * 2  # Extra spacing after name
    
    # Draw info text (each line centered)
    for line in info_lines:
        try:
            line_bbox = draw.textbbox((0, 0), line, font=info_font)
            line_width = line_bbox[2] - line_bbox[0]
            line_height = line_bbox[3] - line_bbox[1]
        except AttributeError:
            line_width, line_height = info_font.getsize(line)
            
        # Center align text horizontally in the box
        line_x = box_x1 + (box_width - line_width) // 2
        draw.text((line_x, current_y), line, fill="rgb(237, 125, 49)", font=info_font)
        current_y += line_height + line_spacing

    # Save and send
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format="JPEG")
    img_byte_arr.seek(0)
    random_number = random.randint(100000, 999999)
    base_url = frappe.utils.get_url()
    file = frappe.get_doc({
        "doctype": "File",
        "file_name": f"anniversary_{name}_{random_number}.png",
        "file_url": f"/files/anniversary_{name}_{random_number}.png",
        "content": img_byte_arr.getvalue(),
        "content_type": "image/jpeg",
        "is_private": 0,
    })
   
    file.insert(ignore_permissions=True)
    frappe.sendmail(
        recipients=[email],
        cc=cc_mail if cc_mail else None,
        subject=f"Happy Work Anniversary to {name}",
        sender=arc_hr_settings.anniversary_sender_email,
        template="birthday",
        args={"img_url": base_url + file.file_url},
        expose_recipients = 'header'
    )
    
    
@frappe.whitelist()
def send_birthday_wish(email="sohan.dev@excelbd.com", name="Sohanur Rahman Lelin Khan", 
                      department="Engineering And Technology", job_location="Baridhara HR"):
    arc_hr_settings = frappe.get_doc("ArcHR Settings")
    cc_mail=frappe.db.get_single_value("ArcHR Settings", "cc_mail")
    cc_mail = cc_mail.split(",")
    birthday_image_path = "assets/excel_hr/birth.jpg"
    font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"

    if not os.path.exists(birthday_image_path):
        frappe.throw(f"File not found at {birthday_image_path}")
    if not os.path.exists(font_path):
        frappe.throw(f"Font file not found at {font_path}")

    # Open the original image
    original_image = Image.open(birthday_image_path)
    
    # Get original dimensions
    original_width, original_height = original_image.size
    
    # Define new dimensions (reducing by 50%)
    # Using a more aggressive reduction factor
    new_width = int(original_width * 0.8)
    new_height = int(original_height * 0.8)
    
    # Resize the image
    image = original_image.resize((new_width, new_height), Image.LANCZOS)
    
    draw = ImageDraw.Draw(image)

    # Adjust font sizes for the smaller image
    name_font_size = 20  # Reduced from 18
    info_font_size = 16  # Reduced from 18
    name_font = ImageFont.truetype(font_path, name_font_size)
    info_font = ImageFont.truetype(font_path, info_font_size)

    # Text content
    name_text = f"{name}"
    department_text = f"{department}"
    location_text = f"{job_location}"

    # Calculate text dimensions
    try:
        # For name text
        name_bbox = draw.textbbox((0, 0), name_text, font=name_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_height = name_bbox[3] - name_bbox[1]
        
        # For department text
        dept_bbox = draw.textbbox((0, 0), department_text, font=info_font)
        dept_width = dept_bbox[2] - dept_bbox[0]
        dept_height = dept_bbox[3] - dept_bbox[1]
        
        # For location text
        loc_bbox = draw.textbbox((0, 0), location_text, font=info_font)
        loc_width = loc_bbox[2] - loc_bbox[0]
        loc_height = loc_bbox[3] - loc_bbox[1]
        
    except AttributeError:
        # Fallback for older Pillow versions
        name_width, name_height = name_font.getsize(name_text)
        dept_width, dept_height = info_font.getsize(department_text)
        loc_width, loc_height = info_font.getsize(location_text)

    # Scale down padding and spacing for the smaller image
    padding = 5  # Reduced from 10
    line_spacing = 7  # Reduced from 5

    # Calculate total box width and height
    box_width = max(name_width, dept_width, loc_width) + 2 * padding
    box_height = name_height + dept_height + loc_height + 3 * padding + 2 * line_spacing

    # Scale the box position for the resized image
    box_x1 = int(48 * (new_width / original_width))
    box_y1 = (image.height - box_height) // 1.82
    box_x2 = box_x1 + box_width
    box_y2 = box_y1 + box_height
    
    # Draw the single box
    # draw.rectangle((box_x1, box_y1, box_x2, box_y2), fill="rgb(237, 125, 49)")
    
    # Draw name text
    name_text_x = box_x1 + padding
    current_y = box_y1 + padding
    draw.text((name_text_x, current_y), name_text, fill="rgb(237, 125, 49)", font=name_font)
    
    # Update vertical position for department text
    current_y += name_height + line_spacing
    
    # Draw department text
    dept_x = box_x1 + padding
    draw.text((dept_x, current_y), department_text, fill="rgb(237, 125, 49)", font=info_font)
    
    # Update vertical position for location text
    current_y += dept_height + line_spacing
    
    # Draw location text
    loc_x = box_x1 + padding
    draw.text((loc_x, current_y), location_text, fill="rgb(237, 125, 49)", font=info_font)
    
    # Save and send
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG', quality=85)  # Reduced quality for smaller file size
    img_byte_arr.seek(0)
    
    random_number = random.randint(100000, 999999)
    base_url = frappe.utils.get_url()
    
    file = frappe.get_doc({
        "doctype": "File",
        "file_name": f"birthday_{name}_{random_number}.png",
        "file_url": f"/files/birthday_{name}_{random_number}.png",
        "content": img_byte_arr.getvalue(),
        "content_type": "image/jpeg",
        "is_private": 0,
    })
    
    file.insert(ignore_permissions=True)
    
    frappe.sendmail(
        recipients=email,
        subject=f"Happy Birthday to {name}",
        cc=cc_mail if cc_mail else None,
        sender=arc_hr_settings.birthday_sender_email,
        template="birthday",
        args={
            "img_url": base_url + file.file_url,
        },
        expose_recipients = 'header',
    )



import frappe
from frappe import _
from frappe.utils import nowdate, getdate
@frappe.whitelist()
def get_employee_overview(email):
    if not email:
        frappe.throw(_("Email is required"))

    query = """
    SELECT 
        emp.employee,
        emp.employee_name,
        emp.company_email,
        lle.leave_type,

        -- Leave Ledger Summary
        SUM(CASE WHEN lle.transaction_type = 'Leave Allocation' THEN lle.leaves ELSE 0 END) AS total_allocated,
        SUM(CASE WHEN lle.transaction_type = 'Leave Application' THEN ABS(lle.leaves) ELSE 0 END) AS total_taken,

        -- Remaining Leave
        (SUM(CASE WHEN lle.transaction_type = 'Leave Allocation' THEN lle.leaves ELSE 0 END) - 
        SUM(CASE WHEN lle.transaction_type = 'Leave Application' THEN ABS(lle.leaves) ELSE 0 END)) AS remaining_leave,

        -- Pending Leave Applications (status = 0)
        COALESCE((
            SELECT COUNT(*) 
            FROM `tabLeave Application` la 
            WHERE la.employee = emp.name 
            AND la.docstatus = 0  -- Only pending applications
            AND YEAR(la.from_date) = YEAR(CURDATE())
        ), 0) AS pending_leave_requests,

        -- Pending Attendance Requests (workflow_state = 'Applied')
        COALESCE((
            SELECT COUNT(*) 
            FROM `tabAttendance Request` ar 
            WHERE ar.employee = emp.name 
            AND ar.workflow_state = 'Applied'  -- Only applied requests
            AND YEAR(ar.from_date) = YEAR(CURDATE())
        ), 0) AS pending_attendance_requests

    FROM `tabLeave Ledger Entry` lle
    JOIN `tabEmployee` emp ON lle.employee = emp.name

    WHERE lle.docstatus = 1
    AND YEAR(lle.from_date) = YEAR(CURDATE())
    AND YEAR(lle.to_date) = YEAR(CURDATE())
    AND emp.company_email = %s

    GROUP BY emp.employee, emp.employee_name, emp.company_email, lle.leave_type
    ORDER BY emp.employee, lle.leave_type;
    """

    results = frappe.db.sql(query, (email,), as_dict=True)
    
    if not results:
        frappe.throw(_("No leave records found for this employee."))

    return results

# @frappe.whitelist()
# def attendance_list_with_checkin_and_checkout(from_date=None,to_date=None,filter="zmin"):
#    if not from_date:
#       from_date = datetime.strptime(today(),"%Y-%m-%d")-timedelta(days=2)
#    if not to_date:
#       to_date = datetime.strptime(today(),"%Y-%m-%d")
#    filters={"attendance_date":["between",(from_date,to_date)]}
#    if  filter:
#        filters={"attendance_date":["between",(from_date,to_date)],"employee_name":["like","%"+filter+"%"]}
   

#    attendance_list = frappe.get_list("Attendance",fields=["*"],filters=filters,order_by="creation desc",ignore_permissions=False)
#    for attendance in attendance_list:
#        attendance.checkin_list = frappe.db.get_list("Employee Checkin",filters={"attendance":attendance.name,"log_type":"IN"},fields=["*"],order_by="time asc")
#        attendance.checkout_list = frappe.db.get_list("Employee Checkin",filters={"attendance":attendance.name,"log_type":"OUT"},fields=["*"],order_by="time asc")
#    return attendance_list
@frappe.whitelist()
def attendance_list_with_checkin_and_checkout(
    filters=None, 
    or_filters=None,  # Corrected parameter name here
    order_by=None,
    limit_start=0,
    limit_page_length=10,
    fields=None):
    
    # Check if filters are properly passed
    if filters:
        filters = json.loads(filters) if isinstance(filters, str) else filters
    if or_filters:  # Corrected variable name here
        or_filters = json.loads(or_filters) if isinstance(or_filters, str) else or_filters
    if fields:
        fields = json.loads(fields) if isinstance(fields, str) else fields

    # Fetch attendance records
    attendance_list = frappe.get_list(
        "Attendance",
        fields=fields if fields else ["*"],
        filters=filters if filters else None,
        or_filters=or_filters if or_filters else None,  # Corrected argument here
        order_by=order_by if order_by else "creation desc",
        limit_start=limit_start if limit_start else 0,
        limit_page_length=limit_page_length if limit_page_length else 10,
        ignore_permissions=False
    )

    for attendance in attendance_list:
        # Get first check-in (earliest)
        checkin = frappe.db.get_list(
            "Employee Checkin",
            filters={"attendance": attendance.name,},
            fields=["*"],
            order_by="time asc",  # Ascending order to get the first check-in
            limit=1
        )
        
        # Get last checkout (latest)
        checkout = frappe.db.get_list(
            "Employee Checkin",
            filters={"attendance": attendance.name,},
            fields=["*"],
            order_by="time desc",  # Descending order to get the last check-out
            limit=1
        )

        attendance["checkin_list"] = checkin if checkin else []
        attendance["checkout_list"] = checkout if checkout else []

    return attendance_list
    
@frappe.whitelist()    
def get_permitted_employee():
    employee_list = frappe.get_list("Employee",fields=["name"],filters={"status":"Active"},ignore_permissions=False)
    return employee_list

    
    
    

    
    





    
    
