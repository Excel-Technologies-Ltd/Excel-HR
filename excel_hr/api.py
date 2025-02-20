import frappe
from PIL import Image, ImageDraw, ImageFont
import io
import os
from frappe.utils import get_url
import frappe.utils
import requests
import base64
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
# def send_birthday_wish():
#     email = 'sohan.dev@excelbd.com',
#     name = 'Sohan'
#     """
#     Send birthday wish email with dynamically updated image.
    
#     Args:
#         email (str): The email of the user to whom the wish is being sent.
#         name (str): The name to be added in the birthday image.
#     """

#     # Path to the uploaded image
#     birthday_image_path = "assets/excel_hr/Birthday.jpg"  # Adjust this path if needed

#     # Check if the file exists
#     if not os.path.exists(birthday_image_path):
#         frappe.throw(f"File not found at {birthday_image_path}")

#     # Open the image
#     image = Image.open(birthday_image_path)

#     # Prepare to edit the image
#     draw = ImageDraw.Draw(image)

#     # Define background color (orange)
#     background_color = (255, 165, 0)  # RGB for orange

#     # Use a font (you can replace this with a custom font if needed)
#     font = ImageFont.load_default()  # Use a default font or specify your own

#     # Calculate the bounding box of the name text
#     text_bbox = draw.textbbox((0, 0), f"Mr. {name}", font=font)
#     text_width = text_bbox[2] - text_bbox[0]  # width of the text
#     text_height = text_bbox[3] - text_bbox[1]  # height of the text

#     # Calculate the rectangle's position to center it
#     rect_x1 = (image.width - text_width) // 2 - 10  # Adding some padding
#     rect_y1 = 50  # Adjust as necessary for vertical positioning
#     rect_x2 = rect_x1 + text_width + 20  # Adding some padding
#     rect_y2 = rect_y1 + 20  # Height of the rectangle (20px)

#     # Draw the orange rectangle centered around the name
#     draw.rectangle([rect_x1, rect_y1, rect_x2, rect_y2], fill=background_color)

#     # Position of the name in the middle of the rectangle
#     name_position = ((image.width - text_width) // 2, rect_y1 + (rect_y2 - rect_y1 - text_height) // 2)

#     # Draw the name on the image
#     draw.text(name_position, f"Mr. {name}", fill="black", font=font)

#     # Save the updated image to a BytesIO object
#     img_byte_arr = io.BytesIO()
#     image.save(img_byte_arr, format='PNG')
#     img_byte_arr.seek(0)

#     # Send an email with the updated image attached
#     frappe.sendmail(
#         recipients=email,
#         subject="Happy Birthday!",
#         message=f"Dear Mr. {name},\n\nWishing you a lovely birthday and a great life ahead. Keep smiling!",
#         attachments=[{
#             "fname": f"birthday_{name}.png",
#             "fcontent": img_byte_arr.getvalue(),
#         }]
#     )
    
    



    
    
import frappe
import os
import io
from PIL import Image, ImageDraw, ImageFont

@frappe.whitelist()
def send_birthday_wish2():
    email = 'sohan.dev@excelbd.com'
    name = 'Sohanur Rahman Lelin'
    """
    Send birthday wish email with dynamically updated image.
    
    Args:
        email (str): The email of the user to whom the wish is being sent.
        name (str): The name to be added in the birthday image.
    """

    # Path to the uploaded image
    birthday_image_path = "assets/excel_hr/Birthday.jpg" 
    font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"# Adjust this path if needed

    # Check if the file exists
    if not os.path.exists(birthday_image_path):
        frappe.throw(f"File not found at {birthday_image_path}")

    # Open the image
    image = Image.open(birthday_image_path)

    # Prepare to edit the image
    draw = ImageDraw.Draw(image)

    # Load the default font
    font = ImageFont.load_default()

    # Set the desired font size (approximate method by scaling the default font)
    font_size = 100  # Set the desired size of the text

    # Scaling factor (approximate size adjustment)
    # The default font is quite small, so we simulate a larger font by scaling it manually


    # Scale the font size

    # Calculate the text's width and height for positioning
    text = f"{name}"
    
    font_size = ImageFont.truetype(font_path,80)
    # Position the text at the center
    text_position = ((image.width ) // 13, (image.height) // 2)
 # Set the background color of the text (e.g., yellow)
   

    # Draw the name on the image
    draw.text(text_position, text, fill="#ed7d31", font=font_size)

    # Save the updated image to a BytesIO object
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    import base64
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    # Send an email with the updated image attached
    frappe.sendmail(
        recipients=email,
        subject="Happy Birthday!",
        message=f"""
            <p>Dear Mr. {name},</p>
            <p>Wishing you a lovely birthday and a great life ahead. Keep smiling!</p>
             <img src="data:image/png;base64,{img_base64}" alt="Birthday Image" style="width:100%; max-width:600px;"/>
        """,
        attachments=[{
            "fname": f"birthday_{name}.png",
            "fcontent": img_byte_arr.getvalue(),
        }],
        delayed=False
    )
    
 
import frappe
import os
import io
from PIL import Image, ImageDraw, ImageFont

@frappe.whitelist()
def send_birthday_wish3():
    email = 'sohan.dev@excelbd.com'
    name = 'Sohanur Rahman Lelin'
    """
    Send birthday wish email with dynamically updated image.
    
    Args:
        email (str): The email of the user to whom the wish is being sent.
        name (str): The name to be added in the birthday image.
    """

    # Path to the uploaded image
    birthday_image_path = "assets/excel_hr/Birthday.jpg" 
    font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"# Adjust this path if needed

    # Check if the file exists
    if not os.path.exists(birthday_image_path):
        frappe.throw(f"File not found at {birthday_image_path}")

    # Open the image
    image = Image.open(birthday_image_path)

    # Prepare to edit the image
    draw = ImageDraw.Draw(image)

    # Load the default font
    font = ImageFont.load_default()

    # Set the desired font size (approximate method by scaling the default font)
    font_size = 100  # Set the desired size of the text

    # Scaling factor (approximate size adjustment)
    # The default font is quite small, so we simulate a larger font by scaling it manually


    # Scale the font size

    # Calculate the text's width and height for positioning
    text = f"{name}"
    
    font_size = ImageFont.truetype(font_path,80)
    # Position the text at the center
    text_position = ((image.width ) // 13, (image.height) // 2)
 # Set the background color of the text (e.g., yellow)
   

    # Draw the name on the image
    draw.text(text_position, text, fill="#ed7d31", font=font_size)

    # Save the updated image to a BytesIO object
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    import base64
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
    
    # Send an email with the updated image attached
    cid = "birthday_image"
    frappe.sendmail(
        recipients=email,
        subject="Happy Birthday!",
        message=f"""
            <p>Dear Mr. {name},</p>
            <p>Wishing you a lovely birthday and a great life ahead. Keep smiling!</p>
             <img src="cid:{cid}" alt="Birthday Image" style="width:100%; max-width:600px;"/>
        """,
        attachments=[{
            "fname": f"birthday_{name}.png",
            "fcontent": img_byte_arr.getvalue(),
            "content_id": cid,
            "content_type": "image/png",
            "inline": True,
        }],
        delayed=False
    )   



import frappe
import os
import io
from PIL import Image, ImageDraw, ImageFont
import base64
import random

@frappe.whitelist()
def send_birthday_wish():
    email = 'sohan.dev@excelbd.com'  # Replace with actual email
    name = 'Sohanur Rahman Lelin'  # Replace with actual name

    birthday_image_path = "assets/excel_hr/Birthday.jpg"
    font_path = "assets/excel_hr/Ubuntu/Ubuntu-Bold.ttf"

    if not os.path.exists(birthday_image_path):
        frappe.throw(f"File not found at {birthday_image_path}")
    if not os.path.exists(font_path):
        frappe.throw(f"Font file not found at {font_path}")

    image = Image.open(birthday_image_path)
    draw = ImageDraw.Draw(image)

    font_size = 80
    font = ImageFont.truetype(font_path, font_size)

    text = f"{name}"

    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        text_width, text_height = font.getsize(text)

    padding = 20
    bg_width = text_width + 2 * padding
    bg_height = text_height + 2 * padding

    bg_x1 = (image.width - bg_width) // 8
    bg_y1 = (image.height - bg_height) // 1.9
    bg_x2 = bg_x1 + bg_width
    bg_y2 = bg_y1 + bg_height

    # text_x = bg_x1 + (bg_width - text_width) // 2
    # text_y = bg_y1 + (bg_height - text_height) // 2
    text_x = bg_x1 + padding  # Use text_padding here
    text_y = bg_y1 + 3   # Use text_padding here

    draw.rectangle((bg_x1, bg_y1, bg_x2, bg_y2), fill="#ed7d31")
    draw.text((text_x, text_y), text, fill="black", font=font)

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
   
    img_byte_arr.seek(0)
    random_number = random.randint(100000, 999999)
    base_url = frappe.utils.get_url()
    file = frappe.get_doc({
        'doctype': 'File',
        'file_name': f'birthday_{name}_{random_number}.png',
        'file_url': '/files/birthday_{name}_{random_number}.png', 
        'content': img_byte_arr.getvalue(),
        'content_type': 'image/png',
        # Associate with the recipient's email (or a relevant field)
        'is_private': 0,
        'optimize_for_web': 1,
        
    })
    file.insert()
    cid = "birthday_image"
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')

    frappe.sendmail(
        recipients=email,
        subject="Happy Birthday!",
        # message=f"""
        #     <p>Dear Mr. {name},</p>
        #     <p>Wishing you a lovely birthday and a great life ahead. Keep smiling!</p>
        #     <img src="data:image/png;base64,{img_base64}" alt="Birthday Image" style="width:100%; max-width:600px;"/>
        # """,
        template="birthday",
        args={
            "img_url": base_url + file.file_url,
            "name": name
        },
        # attachments=[{
        #     "fname": f"birthday_{name}.png",
        #     "fcontent": img_byte_arr.getvalue(),
        #     "content_id": cid,
        #     "content_type": "image/png",
        #     "inline": True,
           
        # }],
        delayed=False
    )




