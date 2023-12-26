// Copyright (c) 2023, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

// For license information, please see license.txt
/* eslint-disable */

  
 
  
  // set_options for excel_subsection
  
  
  // excel job location
  
  
  
  
  
  // Copyright (c) 2023, Shaid Azmin and contributors
  // For license information, please see license.txt
  /* eslint-disable */
  
  frappe.query_reports["Excel Leave Analysis"] = {
	filters: [
	  {
		fieldname: "date",
		label: __("Date"),
		fieldtype: "Date",
		reqd: 1,
		default: frappe.datetime.year_end(),
	  },
	//   {
	// 	fieldname: "date_range",
	// 	label: __("Date Range"),
	// 	fieldtype: "Date Range",
	// 	reqd: 1,
	// 	default: [frappe.datetime.year_start(), frappe.datetime.month_end()],
	//   },
	  {
		fieldname: "company",
		label: __("Company"),
		fieldtype: "Link",
		options: "Company",
		reqd: 1,
		default: frappe.defaults.get_user_default("Company"),
	  },
	  // here employee i want multiselect
	  {
		fieldname: "employee",
		label: __("Employee"),
		fieldtype: "MultiSelectList",
		get_data: function (txt) {
		  return frappe.db.get_link_options("Employee", txt);
		},
	  },
	
	  {
		fieldname: "excel_department",
		label: __("Parent Department"),
		fieldtype: "Link",
		options: 'Department',
		
	  },
  
	  {
		fieldname: "excel_section",
		label: __("Section"),
		fieldtype: "Link",
		options: 'Department',
		get_query: function() {
			var main_department = frappe.query_report.get_filter_value('excel_department');
			if (main_department) {
				return {
					filters: {
						parent_department: main_department
					}
				};
			} else {
				// If the parent value is not selected, show all departments
				return {};
			}
		}
		
	  },
  
	  {
		fieldname: "excel_sub_section",
		label:__("Sub Section"),
		fieldtype: "Link",
		options: 'Department',
		get_query: function() {
			var main_department = frappe.query_report.get_filter_value('excel_section');
			if (main_department) {
				return {
					filters: {
						parent_department: main_department
					}
				};
			} else {
				// If the parent value is not selected, show all departments
				return {};
			}
		}
		
		  
	  },
	  {
		fieldname: "excel_job_location",
		label: __("Excel Job Location"),
		fieldtype: "Select",
		options: [
		"",
		{ value: 'Head Office', label:__( 'Head Office' )},
		{ value: 'Corporate Office', label:__( 'Corporate Office' )},
		{ value: 'Dhanmondi Warehouse', label:__( 'Dhanmondi Warehouse' )},
		{ value: 'IDB', label:__( 'IDB' )},
		{ value: 'Multiplan', label:__( 'Multiplan' )},
		{ value: 'CCSP-Multiplan', label:__( 'CCSP-Multiplan' )},
		{ value: 'Uttara', label:__( 'Uttara' )},
		{ value: 'Motijheel Zone', label:__( 'Motijheel Zone' )},
		{ value: 'CSP-Motijheel', label:__( 'CSP-Motijheel' )},
		{ value: 'CSP-Gulistan', label:__( 'CSP-Gulistan' )},
		{ value: 'Gulistan Zone', label:__( 'Gulistan Zone' )},
		{ value: 'CTG', label:__( 'CTG' )},
		{ value: 'CSP-Uttara', label:__( 'CSP-Uttara' )},
		{ value: 'Khulna Zone', label:__( 'Khulna Zone' )},
		{ value: 'Bogura Zone', label:__( 'Bogura Zone' )},
		{ value: 'Dhanmondi Zone', label:__( 'Dhanmondi Zone' )},
		{ value: 'Sylhet Zone', label:__( 'Sylhet Zone' )},
		{ value: 'CSP-Bogura', label:__( 'CSP-Bogura' )},
		{ value: 'Rangpur Zone', label:__( 'Rangpur Zone' )},
		{ value: 'CSP-CTG', label:__( 'CSP-CTG' )},
		{ value: 'Faridpur Zone', label:__( 'Faridpur Zone' )},
		{ value: 'Rajshahi Zone', label:__( 'Rajshahi Zone' )},
		{ value: 'Mymensingh Zone', label:__( 'Mymensingh Zone' )},
		{ value: 'Feni Zone', label:__( 'Feni Zone' )},
		{ value: 'CSP-Rangpur', label:__( 'CSP-Rangpur' )},
		{ value: 'Barishal Zone', label:__( 'Barishal Zone' )},
		{ value: 'CSP-Sylhet', label:__( 'CSP-Sylhet' )},
		{ value: 'CSP-Khulna', label:__( 'CSP-Khulna' )},
		{ value: 'CSP-IDB', label:__( 'CSP-IDB' )},
		{ value: 'Kusthia Zone', label:__( 'Kusthia Zone' )},
		{ value: 'Savar Zone', label:__( 'Savar Zone' )},
		{ value: 'Gazipur Zone', label:__( 'Gazipur Zone' )},
		{ value: 'CSP-Rajshahi', label:__( 'CSP-Rajshahi' )},
		{ value: 'Dinajpur Zone', label:__( 'Dinajpur Zone' )},
		{ value: 'Noakhali Zone', label:__( 'Noakhali Zone' )},
		{ value: 'Narayanganj Zone', label:__( 'Narayanganj Zone' )},
		{ value: 'Pabna Zone', label:__( 'Pabna Zone' )},
		{ value: 'CSP-Feni', label:__( 'CSP-Feni' )},
		{ value: 'Tangail Zone', label:__( 'Tangail Zone' )},
		{ value: 'CSP-Mymensingh', label:__( 'CSP-Mymensingh' )},
		{ value: 'E. Road Zone', label:__( 'E. Road Zone' )},
		{ value: 'CSP-Gazipur', label:__( 'CSP-Gazipur' )},
		{ value: 'CTG Corporate', label:__( 'CTG Corporate' )},
		{ value: 'CTG Zone', label:__( 'CTG Zone' )},
		{
		  value: 'Bangabandhu Hi-Tech City',
		  label:__( 'Bangabandhu Hi-Tech City')
		},
		{ value: 'Bogra Zone', label:__( 'Bogra Zone') },
		{ value: 'CSP-Barishal', label:__( 'CSP-Barishal') }
	],
	  },
	  {
		fieldname: "leave_type",
		label: __("Leave Type"),
		fieldtype: "MultiSelectList",
		get_data: function (txt) {
		  return frappe.db.get_link_options("Leave Type", txt);
		},
	  },
	  {
		fieldname: "employee_status",
		label: __("Employee Status"),
		fieldtype: "Select",
		options: [
		  "",
		  { value: "Active", label: __("Active") },
		  { value: "Inactive", label: __("Inactive") },
		  { value: "Suspended", label: __("Suspended") },
		  { value: "Left", label: __("Left") },
		],
		default: "Active",
	  },
	],
  };
  