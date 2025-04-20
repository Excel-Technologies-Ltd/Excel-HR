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

    cc_mail = frappe.db.get_single_value("Excel Alert Settings", "cc_mail")
    
    
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
        template="birthday",
        args={"img_url": base_url + file.file_url},
        expose_recipients = 'header'
    )
    
    
@frappe.whitelist()
def send_birthday_wish(email="sohan.dev@excelbd.com", name="Sohanur Rahman Lelin Khan", 
                      department="Engineering And Technology", job_location="Baridhara HR"):
    cc_mail=frappe.db.get_single_value("Excel Alert Settings", "cc_mail")
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

@frappe.whitelist()
def attendance_list_with_checkin_and_checkout(from_date=None,to_date=None):
   if not from_date:
      from_date = datetime.strptime(today(),"%Y-%m-%d")-timedelta(days=2)
   if not to_date:
      to_date = datetime.strptime(today(),"%Y-%m-%d")

   attendance_list = frappe.get_list("Attendance",fields=["*"],filters={"attendance_date":["between",(from_date,to_date)]},order_by="creation desc",ignore_permissions=False)
   for attendance in attendance_list:
       attendance.checkin_list = frappe.db.get_list("Employee Checkin",filters={"attendance":attendance.name,"log_type":"IN"},fields=["*"],order_by="time asc")
       attendance.checkout_list = frappe.db.get_list("Employee Checkin",filters={"attendance":attendance.name,"log_type":"OUT"},fields=["*"],order_by="time asc")
   return attendance_list
    
@frappe.whitelist()    
def get_permitted_employee():
    employee_list = frappe.get_list("Employee",fields=["name"],filters={"status":"Active"},ignore_permissions=False)
    return employee_list

    
    
    

    
    





    
    
