
# from hrms.hr.doctype.employee_transfer.employee_transfer import EmployeeTransfer as EmployeeTransferBase
# from frappe import _
# import frappe
# from hrms.hr.utils import delete_employee_work_history, get_formatted_value, update_to_date_in_work_history
# from datetime import datetime

# class EmployeeTransfer(EmployeeTransferBase):
# 	def on_submit(self):
# 		employee = frappe.get_doc("Employee", self.employee)
# 		if self.create_new_employee_id:
# 			new_employee = frappe.copy_doc(employee)
# 			new_employee.name = None
# 			new_employee.employee_number = None
# 			new_employee = update_employee_work_history(
# 				new_employee, self.transfer_details, date=self.transfer_date
# 			)
# 			if self.new_company and self.company != self.new_company:
# 				new_employee.internal_work_history = []
# 				new_employee.date_of_joining = self.transfer_date
# 				new_employee.company = self.new_company
# 			# move user_id to new employee before insert
# 			if employee.user_id and not self.validate_user_in_details():
# 				new_employee.user_id = employee.user_id
# 				employee.db_set("user_id", "")
# 			new_employee.insert()
# 			self.db_set("new_employee_id", new_employee.name)
# 			# relieve the old employee
# 			employee.db_set("relieving_date", self.transfer_date)
# 			employee.db_set("status", "Left")
# 		else:
# 			employee = update_employee_work_history(employee, self.transfer_details, date=self.transfer_date)
# 			if self.new_company and self.company != self.new_company:
# 				employee.company = self.new_company
# 				employee.date_of_joining = self.transfer_date
# 			employee.save()

# 	def on_cancel(self):
# 		employee = frappe.get_doc("Employee", self.employee)
# 		if self.create_new_employee_id:
# 			if self.new_employee_id:
# 				frappe.throw(
# 					_("Please delete the Employee {0} to cancel this document").format(
# 						f"<a href='/app/Form/Employee/{self.new_employee_id}'>{self.new_employee_id}</a>"
# 					)
# 				)
# 			# mark the employee as active
# 			employee.status = "Active"
# 			employee.relieving_date = ""
# 		else:
# 			employee = update_employee_work_history(
# 				employee, self.transfer_details, date=self.transfer_date, cancel=True
# 			)
# 		if self.new_company != self.company:
# 			employee.company = self.company
# 		print(employee.as_dict())
# 		employee.save()

# 	def validate_user_in_details(self):
# 		for item in self.transfer_details:
# 			if item.fieldname == "user_id" and item.new != item.current:
# 				return True
# 		return False






# def update_employee_work_history(employee, details, date=None, cancel=False):
# 	if not details:
# 		return employee

# 	internal_work_history = {}
# 	latest_work_history = {}
# 	for item in details:
# 		field = frappe.get_meta("Employee").get_field(item.fieldname)
# 		if not field:
# 			continue

# 		new_value = item.new if not cancel else item.current
# 		new_value = get_formatted_value(new_value, field.fieldtype)
# 		setattr(employee, item.fieldname, new_value)

# 		if item.fieldname in ["custom_job_location", "designation", "excel_parent_department", "excel_hr_section", "excel_hr_sub_section", "employment_type", "employment_sub_type"]:
# 			find_latest_and_set_last_date_or_create_new(employee.internal_work_history, item.fieldname, date, employee.date_of_joining, item.current)
# 			if item.fieldname == "custom_job_location":
# 				internal_work_history["branch"] = item.new
# 			elif item.fieldname == "designation":
# 				internal_work_history["designation"] = item.new
# 			elif item.fieldname == "excel_parent_department":
# 				internal_work_history["custom_parent_department"] = item.new
# 			elif item.fieldname == "excel_hr_section":
# 				internal_work_history["custom_excel_hr_section"] = item.new
# 			elif item.fieldname == "excel_hr_sub_section":
# 				internal_work_history["custom_excel_hr_sub_section"] = item.new
# 			elif item.fieldname == "employment_type":
# 				internal_work_history["custom_employment_type"] = item.new
# 			elif item.fieldname == "custom_employment_sub_type":
# 				internal_work_history["custom_employment_sub_type"] = item.new

# 	if internal_work_history and not cancel:
# 		internal_work_history["from_date"] = date
# 		employee.append("internal_work_history", internal_work_history)

# 	if cancel:
# 		delete_employee_work_history(details, employee, date)

# 	# update_to_date_in_work_history(employee, cancel)

# 	return employee


# def find_latest_and_set_last_date(array, field_name,to_date):
#     """
#     Filter rows by field name and return only the most recently modified row
    
#     Args:
#         array: List of dictionaries
#         field_name: String - the field name to filter by
    
#     Returns:
#         Dictionary - the most recently modified row, or None if no matches
#     """
#     # Filter rows that have the specified field with a value
#     filtered_rows = [
#         row for row in array 
#         if field_name in row 
#         and row[field_name] is not None 
#         and row[field_name] != ""
#     ]
    
#     # Find and return the most recently modified row
#     if filtered_rows:
#         last_modified_row = max(
#             filtered_rows, 
#             key=lambda row: datetime.strptime(row['from_date'], "%Y-%m-%d")
#         )
#         return last_modified_row
    
#     return None




# def find_latest_and_set_last_date_or_create_new(array, field_name, to_date, date_of_joining, old_value):
#     """
#     Filter rows by field name, find the most recent one, and set its to_date.
#     If not found, create a new entry with old_value.
    
#     Args:
#         array: List of dictionaries
#         field_name: String - the field name to filter by
#         to_date: String or date - the to_date value to set
#         date_of_joining: String or date - the from_date for new entry if not found
#         old_value: The old value to set in the field for new entry
    
#     Returns:
#         None - modifies the array in place
#     """
#     # Filter rows that have the specified field with a value
#     filtered_rows = [
#         row for row in array 
#         if field_name in row 
#         and row[field_name] is not None 
#         and row[field_name] != ""
#     ]
    
#     # Find and update only the to_date of the most recently modified row
#     if filtered_rows:
#         last_modified_row = max(
#             filtered_rows, 
#             key=lambda row: datetime.strptime(row['from_date'], "%Y-%m-%d")
#         )
#         # Only edit the to_date field
#         last_modified_row['to_date'] = to_date
#     else:
#         # Create new object with field and old value
#         new_entry = {
#             field_name: old_value,
#             'from_date': date_of_joining,
#             'to_date': to_date
#         }
#         array.append(new_entry)




from hrms.hr.doctype.employee_transfer.employee_transfer import EmployeeTransfer as EmployeeTransferBase
from frappe import _
import frappe
from hrms.hr.utils import delete_employee_work_history, get_formatted_value, update_to_date_in_work_history
from datetime import datetime
from datetime import timedelta
class EmployeeTransfer(EmployeeTransferBase):
	def on_submit(self):
		employee = frappe.get_doc("Employee", self.employee)
		if self.create_new_employee_id:
			new_employee = frappe.copy_doc(employee)
			new_employee.name = None
			new_employee.employee_number = None
			new_employee = update_employee_work_history(
				new_employee, self.transfer_details, date=self.transfer_date
			)
			if self.new_company and self.company != self.new_company:
				new_employee.internal_work_history = []
				new_employee.date_of_joining = self.transfer_date
				new_employee.company = self.new_company
			# move user_id to new employee before insert
			if employee.user_id and not self.validate_user_in_details():
				new_employee.user_id = employee.user_id
				employee.db_set("user_id", "")
			new_employee.insert()
			self.db_set("new_employee_id", new_employee.name)
			# relieve the old employee
			employee.db_set("relieving_date", self.transfer_date)
			employee.db_set("status", "Left")
		else:
			employee = update_employee_work_history(employee, self.transfer_details, date=self.transfer_date)
			if self.new_company and self.company != self.new_company:
				employee.company = self.new_company
				employee.date_of_joining = self.transfer_date
			employee.save()

	def on_cancel(self):
		employee = frappe.get_doc("Employee", self.employee)
		if self.create_new_employee_id:
			if self.new_employee_id:
				frappe.throw(
					_("Please delete the Employee {0} to cancel this document").format(
						f"<a href='/app/Form/Employee/{self.new_employee_id}'>{self.new_employee_id}</a>"
					)
				)
			# mark the employee as active
			employee.status = "Active"
			employee.relieving_date = ""
		else:
			employee = update_employee_work_history(
				employee, self.transfer_details, date=self.transfer_date, cancel=True
			)
		if self.new_company != self.company:
			employee.company = self.company
		print(employee.as_dict())
		employee.save()

	def validate_user_in_details(self):
		for item in self.transfer_details:
			if item.fieldname == "user_id" and item.new != item.current:
				return True
		return False


def update_employee_work_history(employee, details, date=None, cancel=False):
	if not details:
		return employee

	internal_work_history = {}
	
	# Field mapping from employee fields to internal work history fields
	field_mapping = {
		"custom_job_location": "branch",
		"designation": "designation",
		"excel_parent_department": "custom_parent_department",
		"excel_hr_section": "custom_excel_hr_section",
		"excel_hr_sub_section": "custom_excel_hr_sub_section",
		"employment_type": "custom_employment_sub_type",
	}
	
	for item in details:
		field = frappe.get_meta("Employee").get_field(item.fieldname)
		if not field:
			continue

		new_value = item.new if not cancel else item.current
		new_value = get_formatted_value(new_value, field.fieldtype)
		setattr(employee, item.fieldname, new_value)

		if item.fieldname in field_mapping:
			history_field = field_mapping[item.fieldname]
			
			if not cancel:
				# On submit: Update to_date of the latest work history entry or create new entry
				find_latest_and_set_last_date_or_create_new(
					employee, 
					history_field, 
					date, 
					employee.date_of_joining, 
					item.current
				)
				# Add new value to internal_work_history dictionary
				internal_work_history[history_field] = item.new
			else:
				# On cancel: Remove the to_date that was set and delete the entry that was added
				remove_transfer_history(employee, history_field, date)

	if internal_work_history and not cancel:
		internal_work_history["from_date"] = date
		employee.append("internal_work_history", internal_work_history)

	return employee


def find_latest_and_set_last_date_or_create_new(employee, field_name, to_date, date_of_joining, old_value):
	"""
	Filter rows by field name, find the most recent one, and set its to_date.
	If not found, create a new entry with old_value using employee.append().
	
	Args:
		employee: Employee document object
		field_name: String - the field name to filter by (internal work history field name)
		to_date: String or date - the to_date value to set
		date_of_joining: String or date - the from_date for new entry if not found
		old_value: The old value to set in the field for new entry
	
	Returns:
		None - modifies the employee's internal_work_history in place
	"""
	# Convert internal_work_history to list of dicts for filtering
	work_history = []
	for row in employee.internal_work_history:
		# Convert Document object to dict
		row_dict = row.as_dict() if hasattr(row, 'as_dict') else row
		work_history.append(row_dict)
	
	# Filter rows that have the specified field with a value
	filtered_rows = []
	filtered_indices = []
	for idx, row in enumerate(work_history):
		if (field_name in row and 
			row.get(field_name) is not None and 
			row.get(field_name) != ""):
			filtered_rows.append(row)
			filtered_indices.append(idx)
	
	# Find and update only the to_date of the most recently modified row
	if filtered_rows:
		# Find the row with the latest from_date
		max_idx = 0
		max_date = None  # ✅ CHANGED: Initialize as None instead of parsing immediately
		
		for idx, row in enumerate(filtered_rows):
			row_from_date = row.get('from_date')
			
			# ✅ CHANGED: Added type checking before parsing
			if row_from_date:
				if isinstance(row_from_date, str):
					current_date = datetime.strptime(row_from_date, "%Y-%m-%d")
				elif hasattr(row_from_date, 'year'):  # It's a date or datetime object
					current_date = datetime.combine(row_from_date, datetime.min.time()) if hasattr(row_from_date, 'date') and callable(getattr(row_from_date, 'date')) else datetime(row_from_date.year, row_from_date.month, row_from_date.day)
				else:
					current_date = datetime.strptime('1900-01-01', "%Y-%m-%d")
				
				if max_date is None or current_date > max_date:
					max_date = current_date
					max_idx = idx
		
		# ✅ CHANGED: Added null check before updating
		if max_date is not None:
			actual_idx = filtered_indices[max_idx]
			
			# Convert to_date to proper format and subtract 1 day
			if isinstance(to_date, str):
				to_date_obj = datetime.strptime(to_date, "%Y-%m-%d").date()
			elif hasattr(to_date, 'year'):
				to_date_obj = to_date if not hasattr(to_date, 'date') else to_date.date()
			else:
				to_date_obj = datetime.strptime(str(to_date), "%Y-%m-%d").date()
			
			# Subtract 1 day from to_date
			adjusted_to_date = to_date_obj - timedelta(days=1)
			
			# Update the to_date in the original Document object
			employee.internal_work_history[actual_idx].to_date = adjusted_to_date
	else:
		# Create new entry using employee.append() to maintain Document structure
		new_entry = {
			field_name: old_value,
			'from_date': date_of_joining,
			'to_date': to_date
		}
		if old_value:
			employee.append("internal_work_history", new_entry)

def remove_transfer_history(employee, field_name, transfer_date):
	"""
	On cancel: Remove the entry with from_date = transfer_date and clear to_date from previous entry
	
	Args:
		employee: Employee document object
		field_name: String - the field name to filter by (internal work history field name)
		transfer_date: String or date - the transfer date to match
	
	Returns:
		None - modifies the employee's internal_work_history in place
	"""
	# Convert transfer_date to string for comparison
	if isinstance(transfer_date, str):
		transfer_date_str = transfer_date
	else:
		transfer_date_str = transfer_date.strftime("%Y-%m-%d") if hasattr(transfer_date, 'strftime') else str(transfer_date)
	
	# Find and remove the entry that was added during submit (where from_date = transfer_date)
	rows_to_remove = []
	for idx, row in enumerate(employee.internal_work_history):
		row_dict = row.as_dict() if hasattr(row, 'as_dict') else row
		row_from_date = row_dict.get('from_date')
		
		# Convert row_from_date to string for comparison
		if isinstance(row_from_date, str):
			row_from_date_str = row_from_date
		else:
			row_from_date_str = row_from_date.strftime("%Y-%m-%d") if hasattr(row_from_date, 'strftime') else str(row_from_date)
		
		if (field_name in row_dict and 
			row_dict.get(field_name) is not None and 
			row_dict.get(field_name) != "" and
			row_from_date_str == transfer_date_str):
			rows_to_remove.append(idx)
	
	# Remove rows in reverse order to maintain correct indices
	for idx in sorted(rows_to_remove, reverse=True):
		employee.internal_work_history.pop(idx)
	
	# Find the latest remaining entry with this field and clear its to_date
	work_history = []
	for row in employee.internal_work_history:
		row_dict = row.as_dict() if hasattr(row, 'as_dict') else row
		work_history.append(row_dict)
	
	# Filter rows that have the specified field with a value
	filtered_rows = []
	filtered_indices = []
	for idx, row in enumerate(work_history):
		if (field_name in row and 
			row.get(field_name) is not None and 
			row.get(field_name) != ""):
			filtered_rows.append(row)
			filtered_indices.append(idx)
	
	# Find and clear the to_date of the most recent row
	if filtered_rows:
		# Find the row with the latest from_date
		max_idx = 0
		first_from_date = filtered_rows[0].get('from_date', '1900-01-01')
		
		# Convert to datetime for comparison
		if isinstance(first_from_date, str):
			max_date = datetime.strptime(first_from_date, "%Y-%m-%d")
		else:
			max_date = datetime.combine(first_from_date, datetime.min.time()) if hasattr(first_from_date, 'strftime') else datetime.strptime('1900-01-01', "%Y-%m-%d")
		
		for idx, row in enumerate(filtered_rows):
			row_from_date = row.get('from_date', '1900-01-01')
			
			# Convert to datetime for comparison
			if isinstance(row_from_date, str):
				row_date = datetime.strptime(row_from_date, "%Y-%m-%d")
			else:
				row_date = datetime.combine(row_from_date, datetime.min.time()) if hasattr(row_from_date, 'strftime') else datetime.strptime('1900-01-01', "%Y-%m-%d")
			
			if row_date > max_date:
				max_date = row_date
				max_idx = idx
		
		# Get the actual index in the original internal_work_history
		actual_idx = filtered_indices[max_idx]
		
		# Clear the to_date (set to None or empty string)
		employee.internal_work_history[actual_idx].to_date = None