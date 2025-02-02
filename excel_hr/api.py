import frappe

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
