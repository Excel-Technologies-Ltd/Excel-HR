
import frappe
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import zipfile
import os
from datetime import datetime
from frappe.model.document import Document

class BulkVisualGenerate(Document):
	pass







    
    
    



def get_custom_font_path(font_name, bold=False):
    """
    Get font path from site assets folder only (no system fonts)
    
    Args:
        font_name: Name of the font
        bold: Whether to use bold variant
    
    Returns:
        Path to font file or None
    """
    import frappe
    import os
    
    # Custom fonts stored in site assets
    custom_fonts = {
        "Hind Siliguri": {
            "regular": "excel_hr/Fonts/Hind_Siliguri/HindSiliguri-Regular.ttf",
            "bold": "excel_hr/Fonts/Hind_Siliguri/HindSiliguri-Bold.ttf",
        },
        "Roboto":{
            "regular": "excel_hr/Fonts/Roboto_Font/Roboto-Regular.ttf",
            "bold": "excel_hr/Fonts/Roboto_Font/Roboto-Bold.ttf"
        },
        "Unbounded":{
            "regular": "excel_hr/Fonts/Unbounded/Unbounded-Regular.ttf",
            "bold": "excel_hr/Fonts/Unbounded/Unbounded-Bold.ttf"
        },
        "Gilroy":{
            "regular": "excel_hr/Fonts/Gilroy/GILROY-REGULARITALIC.OTF",
            "bold": "excel_hr/Fonts/Gilroy/GILROY-BOLD.OTF"
        }
        # Add more custom fonts here as you upload them
        # Example:
        # "Roboto": {
        #     "regular": "excel_hr/Fonts/Roboto/Roboto-Regular.ttf",
        #     "bold": "excel_hr/Fonts/Roboto/Roboto-Bold.ttf"
        # }
    }
    
    # Check if font exists in custom fonts
    if font_name not in custom_fonts:
        frappe.log_error(f"Font '{font_name}' not found in custom fonts", "Font Not Found")
        return None
    
    # Get the appropriate variant
    font_file = custom_fonts[font_name].get("bold" if bold else "regular")
    
    if not font_file:
        frappe.log_error(f"Font variant not found for '{font_name}'", "Font Variant Not Found")
        return None
    
    # Get full path to the font in site assets
    bench_path = frappe.utils.get_bench_path()
    font_path = os.path.join(bench_path, 'sites', 'assets', font_file)

    
    # font_path = frappe.get_site_path('assets', font_file)
    print("font_path_site", font_path)
    # Check if file exists
    if os.path.exists(font_path):
        print("font_path", font_path)
        return font_path
    else:
        frappe.log_error(f"Font file not found at: {font_path}", "Font File Missing")
        return None

@frappe.whitelist()
def generate_customer_banner(customer_name, customer_address, base_image_path,font_style,):
    """
    Generate a single promotional banner with customer details
    
    Args:
        customer_name: Name of the customer
        customer_address: Address of the customer
        base_image_path: Path to the base template image
        font_style: Font to use (default: Arial)
    
    Returns:
        PIL Image object
    """
    try:
        # Load the base image
        if base_image_path.startswith('/files/'):
            full_path = frappe.get_site_path('public', base_image_path.lstrip('/'))
        else:
            full_path = frappe.get_site_path('public', 'files', base_image_path.lstrip('/'))
        
        img = Image.open(full_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Get font paths based on user selection
        name_font = None
        address_font = None
        
        # Try to load user-selected font
        name_font_path = get_custom_font_path(font_style, bold=True)
        address_font_path = get_custom_font_path(font_style, bold=False)
        
        if name_font_path:
            try:
                name_font = ImageFont.truetype(name_font_path, 40)
            except Exception as e:
                frappe.log_error(f"Error loading name font: {str(e)}")
        
        if address_font_path:
            try:
                address_font = ImageFont.truetype(address_font_path, 28)
                print("address_font", address_font)
            except Exception as e:
                frappe.log_error(f"Error loading address font: {str(e)}")
        

        bottom_section_start = height - 170
        max_name_width = width - 120  # same as address side padding

        # Wrap customer name if needed
        try:
            raw_width = draw.textlength(customer_name, font=name_font)
        except:
            raw_width = len(customer_name) * 20

        name_lines = []

        if raw_width > max_name_width:
            words = customer_name.split()
            current = []
            for w in words:
                test = " ".join(current + [w])
                try:
                    t_w = draw.textlength(test, font=name_font)
                except:
                    t_w = len(test) * 20
                if t_w <= max_name_width:
                    current.append(w)
                else:
                    if current:
                        name_lines.append(" ".join(current))
                    current = [w]
            if current:
                name_lines.append(" ".join(current))
        else:
            name_lines.append(customer_name)

        # Draw customer name (max 2 lines, center aligned)
        for i, line in enumerate(name_lines[:2]):
            try:
                lw = draw.textlength(line, font=name_font)
            except:
                lw = len(line) * 20
            lx = (width - lw) // 2
            ly = bottom_section_start + (i * 35)
            draw.text((lx, ly), line, fill="white", font=name_font,spacing=10)
        

        address_start_y = bottom_section_start + (len(name_lines[:2]) * 35) + 15
        max_width = width - 120
        
        # Wrap address if needed
        try:
            text_width = draw.textlength(customer_address, font=address_font)
        except:
            text_width = len(customer_address) * 10
        
        if text_width > max_width:
            words = customer_address.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                try:
                    test_width = draw.textlength(test_line, font=address_font)
                except:
                    test_width = len(test_line) * 8
                
                if test_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw wrapped lines (max 2 lines) - CENTER ALIGNED
            for i, line in enumerate(lines[:2]):
                try:
                    line_width = draw.textlength(line, font=address_font)
                except:
                    line_width = len(line) * 8
                
                line_x = (width - line_width) // 2
                draw.text((line_x, address_start_y + (i * 35)), line, fill="#CCCCCC", font=address_font,spacing=10)
        else:
            # Single line address - CENTER ALIGNED
            address_x = (width - text_width) // 2
            draw.text((address_x, address_start_y), customer_address, fill="#CCCCCC", font=address_font)
        
        return img
        
    except Exception as e:
        frappe.log_error(f"Error generating banner: {str(e)}", "Banner Generation Error")
        raise


@frappe.whitelist()
def generate_bulk_banners(customers_data, base_image_path=None,font_style=None):
    """
    Generate banners for multiple customers and return as ZIP file
    
    Args:
        customers_data: JSON string or list of dicts with 'name' and 'address' keys
        base_image_path: Path to the base template image (optional)
    
    Returns:
        dict with file_url to download ZIP
    """
    try:
        # Parse customers_data if it's a JSON string
        if isinstance(customers_data, str):
            import json
            customers_data = json.loads(customers_data)
        
        if not customers_data or not isinstance(customers_data, list):
            return {
                "success": False,
                "message": "Invalid customers_data. Please provide a list of customers."
            }
        
        # Use default base image if not provided
        if not base_image_path:
            base_image_path = "/files/product_banner_template.png"
        
        # Verify base image exists
        if base_image_path.startswith('/files/'):
            full_path = frappe.get_site_path('public', base_image_path.lstrip('/'))
        else:
            full_path = frappe.get_site_path('public', 'files', base_image_path.lstrip('/'))
        
        if not os.path.exists(full_path):
            return {
                "success": False,
                "message": f"Base image not found at: {full_path}"
            }
        
        # Create a BytesIO object for ZIP file
        zip_buffer = io.BytesIO()
        successful_count = 0
        
        # Create ZIP file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            for idx, customer in enumerate(customers_data, 1):
                customer_name = customer.get('customer_name', f'Customer_{idx}')
                customer_address = customer.get('customer_address', 'No address provided')
                
                try:
                    # Generate banner for this customer
                    img = generate_customer_banner(
                        customer_name=customer_name,
                        customer_address=customer_address,
                        base_image_path=base_image_path,
                        font_style=font_style
                    )
                    
                    # Save image to buffer as PNG
                    img_buffer = io.BytesIO()
                    img.save(img_buffer, format='PNG', quality=95)
                    img_data = img_buffer.getvalue()
                    
                    # Verify image data is not empty
                    if len(img_data) == 0:
                        frappe.log_error(f"Empty image data for {customer_name}", "Banner Generation")
                        continue
                    
                    # Add to ZIP with sanitized filename
                    safe_filename = "".join(c for c in customer_name if c.isalnum() or c in (' ', '-', '_')).strip()
                    safe_filename = safe_filename.replace(' ', '_')
                    if not safe_filename:
                        safe_filename = f"Customer_{idx}"
                    zip_filename = f"{idx:03d}_{safe_filename}.png"
                    
                    zip_file.writestr(zip_filename, img_data)
                    successful_count += 1
                    
                except Exception as e:
                    error_msg = f"Error generating banner for {customer_name}: {str(e)}"
                    frappe.log_error(error_msg, "Banner Generation Error")
                    continue
        
        # Verify ZIP has content
        zip_buffer.seek(0)
        zip_content = zip_buffer.getvalue()
        
        if len(zip_content) == 0 or successful_count == 0:
            return {
                "success": False,
                "message": "Failed to generate any banners. Check error logs for details."
            }
        
        # Save ZIP file to Frappe
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"customer_banners_{timestamp}.zip"
        
        # Create file document
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": zip_filename,
            "is_private": 0,
            "content": zip_content,
            "folder": "Home"
        })
        file_doc.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "file_url": file_doc.file_url,
            "file_name": zip_filename,
            "total_customers": len(customers_data),
            "successful": successful_count,
            "message": f"Successfully generated {successful_count} out of {len(customers_data)} banners"
        }
        
    except Exception as e:
        error_msg = f"Error generating bulk banners: {str(e)}"
        frappe.log_error(error_msg, "Bulk Banner Generation Error")
        return {
            "success": False,
            "message": str(e)
        }


@frappe.whitelist()
def generate_banners_from_customer_doctype(customer_names=None, filters=None):
    """
    Generate banners for customers from Customer DocType
    
    Args:
        customer_names: List of customer names (optional)
        filters: Dict of filters to fetch customers (optional)
    
    Returns:
        dict with file_url to download ZIP
    """
    try:
        customers_data = []
        
        if customer_names:
            # Parse if it's a JSON string
            if isinstance(customer_names, str):
                import json
                customer_names = json.loads(customer_names)
            
            # Fetch specific customers
            for customer_name in customer_names:
                customer_doc = frappe.get_doc("Customer", customer_name)
                address = get_customer_address(customer_doc)
                
                customers_data.append({
                    "name": customer_doc.customer_name or customer_name,
                    "address": address
                })
        
        elif filters:
            # Parse if it's a JSON string
            if isinstance(filters, str):
                import json
                filters = json.loads(filters)
            
            # Fetch customers based on filters
            customers = frappe.get_all("Customer", filters=filters, fields=["name", "customer_name"])
            
            for customer in customers:
                customer_doc = frappe.get_doc("Customer", customer.name)
                address = get_customer_address(customer_doc)
                
                customers_data.append({
                    "name": customer_doc.customer_name or customer.name,
                    "address": address
                })
        
        else:
            return {
                "success": False,
                "message": "Please provide either customer_names or filters"
            }
        
        # Generate banners
        return generate_bulk_banners(customers_data)
        
    except Exception as e:
        frappe.log_error(f"Error generating banners from Customer doctype: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }


def get_customer_address(customer_doc):
    """
    Get formatted address for a customer
    """
    try:
        # Try to get primary address
        if customer_doc.customer_primary_address:
            address_doc = frappe.get_doc("Address", customer_doc.customer_primary_address)
            address_parts = []
            
            if address_doc.address_line1:
                address_parts.append(address_doc.address_line1)
            if address_doc.address_line2:
                address_parts.append(address_doc.address_line2)
            if address_doc.city:
                address_parts.append(address_doc.city)
            if address_doc.country:
                address_parts.append(address_doc.country)
            
            return ", ".join(address_parts)
        
        # Fallback: try to get any linked address
        addresses = frappe.get_all(
            "Dynamic Link",
            filters={
                "link_doctype": "Customer",
                "link_name": customer_doc.name,
                "parenttype": "Address"
            },
            fields=["parent"]
        )
        
        if addresses:
            address_doc = frappe.get_doc("Address", addresses[0].parent)
            address_parts = []
            
            if address_doc.address_line1:
                address_parts.append(address_doc.address_line1)
            if address_doc.city:
                address_parts.append(address_doc.city)
            if address_doc.country:
                address_parts.append(address_doc.country)
            
            return ", ".join(address_parts)
        
        return "No address available"
        
    except Exception as e:
        return "Address not found"
    
    
    
    
    