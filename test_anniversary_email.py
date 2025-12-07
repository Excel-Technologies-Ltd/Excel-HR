#!/usr/bin/env python3
"""Test script to generate work anniversary email HTML"""

import frappe
from frappe.utils import getdate
from excel_hr.reminders import count_anniversary_year, get_ordinal_suffix
from datetime import datetime, date

def test_work_anniversary_email():
    """Generate test HTML for work anniversary email"""

    # Create sample employee data matching the actual structure
    sample_employees = {
        "Excel Technologies Ltd.": [
            {
                "name": "Shaid Azmin",
                "image": None,
                "department": "Software Development",
                "location": "HQ Baridhara",
                "years": "3rd",
                "user_id": "azmin@excelbd.com"
            },
            {
                "name": "Md. Mosfiqur Rahman",
                "image": None,
                "department": "Corporate Sales",
                "location": "HQ Baridhara",
                "years": "5th",
                "user_id": "mosfiqur@excelbd.com"
            },
            {
                "name": "John Doe",
                "image": None,
                "department": "Marketing",
                "location": "Branch Office",
                "years": "10th",
                "user_id": "john@excelbd.com"
            }
        ]
    }

    # Get the template
    template_path = frappe.get_app_path("excel_hr", "templates", "emails", "work_anniversary.html")

    with open(template_path, 'r') as f:
        template_content = f.read()

    # Render the template
    from jinja2 import Template
    template = Template(template_content)

    html_output = template.render(
        employees=sample_employees,
        today=getdate()
    )

    # Save to file
    output_path = "/workspace/development/frappe-bench/apps/excel_hr/work_anniversary_test_output.html"
    with open(output_path, 'w') as f:
        f.write(html_output)

    print(f"✅ Test HTML generated successfully!")
    print(f"📄 Output saved to: {output_path}")
    print(f"\n📊 Test data:")
    print(f"   - Company: Excel Technologies Ltd.")
    print(f"   - Total employees: {len(sample_employees['Excel Technologies Ltd.'])}")
    for emp in sample_employees['Excel Technologies Ltd.']:
        print(f"   - {emp['name']}: {emp['years']} anniversary, {emp['department']}, {emp['location']}")

    return output_path

if __name__ == "__main__":
    test_work_anniversary_email()
