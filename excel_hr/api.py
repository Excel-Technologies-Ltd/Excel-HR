import frappe
from PIL import Image, ImageDraw, ImageFont
import io
import os
from frappe.utils import get_url
import frappe.utils
import requests
import base64
import random
from frappe import _
from hrms.controllers.employee_reminders import send_birthday_reminders
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




# @frappe.whitelist()
# def send_birthday_wish(email="sohan.dev@excelbd.com",name="Mr . Sohanur Rahman Lelin Khan"):
#     cc_mail=frappe.db.get_single_value("Excel Alert Settings", "cc_mail")

#     birthday_image_path = "assets/excel_hr/birth.jpg"
#     font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"

#     if not os.path.exists(birthday_image_path):
#         frappe.throw(f"File not found at {birthday_image_path}")
#     if not os.path.exists(font_path):
#         frappe.throw(f"Font file not found at {font_path}")

#     image = Image.open(birthday_image_path)
#     draw = ImageDraw.Draw(image)

#     font_size = 22
#     font = ImageFont.truetype(font_path, font_size)

#     text = f"{name}"

#     try:
#         text_bbox = draw.textbbox((0, 0), text, font=font)
#         text_width = text_bbox[2] - text_bbox[0]
#         text_height = text_bbox[3] - text_bbox[1]
#     except AttributeError:
#         text_width, text_height = font.getsize(text)

#     padding = 7
#     bg_width = text_width + 2 * padding
#     bg_height = text_height + 2 * padding

#     bg_x1 = (image.width - bg_width) // 6.7
#     bg_y1 = (image.height - bg_height) // 1.9
#     bg_x2 = bg_x1 + bg_width
#     bg_y2 = bg_y1 + bg_height
#     text_x = bg_x1 + padding  # Use text_padding here
#     text_y = bg_y1 + 3   # Use text_padding here
#     draw.rectangle((bg_x1, bg_y1, bg_x2, bg_y2), fill="rgb(237, 125, 49)")
#     draw.text((text_x, text_y), text, fill="rgb(0, 0, 0)", font=font)
#     img_byte_arr = io.BytesIO()
#     image.save(img_byte_arr, format='JPEG')
#     img_byte_arr.seek(0)
#     random_number = random.randint(100000, 999999)
#     base_url = frappe.utils.get_url()
#     file = frappe.get_doc({
#         "doctype": "File",
#         "file_name": f"birthday_{name}_{random_number}.png",
#         "file_url": f"/files/birthday_{name}_{random_number}.png",
#         "content": img_byte_arr.getvalue(),
#         "content_type": "image/jpeg",
#         "is_private": 0,
        
#     })
#     file.insert(ignore_permissions=True)
#     frappe.sendmail(
#         recipients=email,
#         subject="Happy Birthday!",
#         cc=cc_mail if cc_mail else None,
#         template="birthday",
#         args={
#             "img_url": base_url + file.file_url,
#         }
#     )







def send_anniversary_wish(email="sohan.dev@excelbd.com",name="Mr. Sohanur Rahman Lelin Khan Mia"):

    cc_mail=frappe.db.get_single_value("Excel Alert Settings", "cc_mail")

    birthday_image_path = "assets/excel_hr/ann.jpg"
    font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"

    if not os.path.exists(birthday_image_path):
        frappe.throw(f"File not found at {birthday_image_path}")
    if not os.path.exists(font_path):
        frappe.throw(f"Font file not found at {font_path}")

    image = Image.open(birthday_image_path)
    draw = ImageDraw.Draw(image)

    font_size = 25
    font = ImageFont.truetype(font_path, font_size)

    text = f"{name}"

    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        text_width, text_height = font.getsize(text)

    padding = 7
    bg_width = text_width + 2 * padding
    bg_height = text_height + 2 * padding

    bg_x1 = (image.width - bg_width) // 1.9
    bg_y1 = (image.height - bg_height) // 1.5
    bg_x2 = bg_x1 + bg_width
    bg_y2 = bg_y1 + bg_height
    text_x = bg_x1 + padding  # Use text_padding here
    text_y = bg_y1 + 3   # Use text_padding here
    draw.rectangle((bg_x1, bg_y1, bg_x2, bg_y2), fill="rgb(237, 125, 49)")
    draw.text((text_x, text_y), text, fill="rgb(0, 0, 0)", font=font)
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
        recipients=email,
        subject="Happy Work Anniversary Greetings!",
        cc=cc_mail if cc_mail else None,
        template="birthday",
        args={"img_url": base_url + file.file_url}
    )
    
    
@frappe.whitelist()
def send_birthday_wish(email="sohan.dev@excelbd.com", name="Sohanur Rahman Lelin Khan"):
    cc_mail=frappe.db.get_single_value("Excel Alert Settings", "cc_mail")

    birthday_image_path = "assets/excel_hr/birth.jpg"
    font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"

    if not os.path.exists(birthday_image_path):
        frappe.throw(f"File not found at {birthday_image_path}")
    if not os.path.exists(font_path):
        frappe.throw(f"Font file not found at {font_path}")

    image = Image.open(birthday_image_path)
    draw = ImageDraw.Draw(image)

    font_size = 22
    font = ImageFont.truetype(font_path, font_size)

    text = f"{name}"

    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        text_width, text_height = font.getsize(text)

    padding = 7
    bg_width = text_width + 2 * padding
    bg_height = text_height + 2 * padding

    # Fixed position from the left edge to align with the red line
    bg_x1 = 50  # Align with the left edge (red line)
    bg_y1 = (image.height - bg_height) // 1.9
    bg_x2 = bg_x1 + bg_width
    bg_y2 = bg_y1 + bg_height
    
    text_x = bg_x1 + padding
    text_y = bg_y1 + 3
    
    draw.rectangle((bg_x1, bg_y1, bg_x2, bg_y2), fill="rgb(237, 125, 49)")
    draw.text((text_x, text_y), text, fill="rgb(0, 0, 0)", font=font)
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
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
        subject="Happy Birthday Greetings!",
        cc=cc_mail if cc_mail else None,
        template="birthday",
        args={
            "img_url": base_url + file.file_url,
        }
    )



import frappe
from frappe import _
from frappe.utils import nowdate, getdate

def get_employee_overview(email):
    if not email:
        frappe.throw(_("Email is required"))
    
    current_year = getdate(nowdate()).year
    
    query = """
    SELECT 
        emp.employee,
        emp.employee_name,
        emp.company_email,
        lle.leave_type,
        
        SUM(CASE WHEN lle.transaction_type = 'Leave Allocation' THEN lle.leaves ELSE 0 END) AS total_allocated,
        SUM(CASE WHEN lle.transaction_type = 'Leave Application' THEN lle.leaves ELSE 0 END) AS total_taken,
        SUM(CASE WHEN lle.is_expired = 1 THEN lle.leaves ELSE 0 END) AS total_expired,
        (SUM(CASE WHEN lle.transaction_type = 'Leave Allocation' THEN lle.leaves ELSE 0 END) - 
         SUM(CASE WHEN lle.transaction_type = 'Leave Application' THEN lle.leaves ELSE 0 END) - 
         SUM(CASE WHEN lle.is_expired = 1 THEN lle.leaves ELSE 0 END)) AS closing_balance,
        
        COALESCE((
            SELECT SUM(la.total_leave_days) 
            FROM `tabLeave Application` la 
            WHERE la.employee = emp.name 
            AND la.docstatus = 0
            AND YEAR(la.from_date) = %(current_year)s
        ), 0) AS pending_leave_days,
        
        COALESCE((
            SELECT COUNT(*) 
            FROM `tabAttendance Request` ar 
            WHERE ar.employee = emp.name 
            AND ar.docstatus = 0
            AND YEAR(ar.from_date) = %(current_year)s
        ), 0) AS pending_attendance_requests
    
    FROM `tabLeave Ledger Entry` lle
    JOIN `tabEmployee` emp ON lle.employee = emp.name
    
    WHERE lle.docstatus = 1
    AND YEAR(lle.from_date) = %(current_year)s
    AND YEAR(lle.to_date) = %(current_year)s
    AND emp.company_email = %(email)s
    
    GROUP BY emp.employee, emp.employee_name, emp.company_email, lle.leave_type
    ORDER BY emp.employee, lle.leave_type;
    """
    
    results = frappe.db.sql(query, {"email": email, "current_year": current_year}, as_dict=True)
    
    if not results:
        return {"message": _("No data found for the given email")}
    
    return results

