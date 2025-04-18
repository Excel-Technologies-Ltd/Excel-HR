# Copyright (c) 2025, Shaid Azmin and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ExcelAlertSettings(Document):
    def before_save(self):
       if self.cc_mail:
           ccmails = self.cc_mail.split(",")

           for mail in ccmails:
               if not frappe.utils.validate_email_address(mail):
                   frappe.throw("Invalid email address: {}".format(mail))
            

