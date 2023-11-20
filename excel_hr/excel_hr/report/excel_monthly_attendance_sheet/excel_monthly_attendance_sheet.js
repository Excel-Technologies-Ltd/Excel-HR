// Copyright (c) 2023, Shaid Azmin and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Excel Monthly Attendance Sheet"] = {
	filters: [],
  };
  // Copyright (c) 2023, Shaid Azmin and contributors
  // For license information, please see license.txt
  /* eslint-disable */
  const excel_sections = [
	"HO-Sales",
	"HiK Vision",
	"IDB-Sales",
	"Multiplan-Sales",
	"Treasury",
	"Digital-X & Logitech",
	"Zone Sales-2",
	"HO-Accounts",
	"Credit Management",
	"Multiplan-Inventory",
	"Uttara-Sales",
	"Zone Sales-1",
	"RMA-Return Material Authorization",
	"Lenovo",
	"IDB CSP-Inventory",
	"TP-Link",
	"CCSP-Support Engineering",
	"Central Warehouse-Driver",
	"CCSP-Repair",
	"Motijheel-Sales",
	"HO-Support Staff",
	"HO-Driver",
	"CCSP-IT & Network",
	"Zone Sales-3",
	"Motijheel CSP-Printer",
	"Gulistan CSP-Support Staff",
	"Administration",
	"HO-Delivery & Collection",
	"Gulistan-Sales",
	"CTG-Sales",
	"CCSP-Support Staff",
	"Uttara CSP-Repair",
	"Khulna-Sales",
	"Bogura-Sales",
	"Dhanmondi-Sales",
	"Sylhet-Sales",
	"Inventory Audit",
	"Gulistan CSP-Repair",
	"VAT & Tax",
	"Inventory Management",
	"Bogura CSP-IT & Network",
	"Rangpur-Sales",
	"HO-Front Desk",
	"CTG CSP-Printer",
	"Epson",
	"Faridpur-Sales",
	"CCSP-Printer",
	"Uttara-Accounts",
	"Rajshahi-Sales",
	"CTG-Delivery & Collection",
	"Mymensingh-Sales",
	"Feni-Sales",
	"Rangpur CSP-Support Staff",
	"Barishal-Sales",
	"Bogura CSP-Support Staff",
	"New Frontier",
	"Sylhet CSP-Support Staff",
	"Khulna CSP-Repair",
	"SI-Sales",
	"MD’s Secretariat",
	"IDB CSP-Support Staff",
	"Motijheel CSP-Support Staff",
	"Central Warehouse-Billing",
	"CTG-Accounts",
	"IDB-Inventory",
	"Multipan-Accounts",
	"Kusthia-Sales",
	"Zone Sales-4",
	"Savar-Sales",
	"IDB CSP-Printer",
	"FTTx",
	"Uttara-Inventory",
	"CTG-Support Staff",
	"Multiplan Sales",
	"Rajshahi CSP-Support Engineering",
	"Supply Chain Management",
	"HO-Cook",
	"Central Warehouse-Cleaner",
	"Dinajpur-Sales",
	"CTG-Driver",
	"Khulna CSP-Support Staff",
	"Motijheel CSP-Accounts",
	"Central Warehouse-Accounts",
	"Project",
	"IDB-Accounts",
	"MIS",
	"Pabna-Sales",
	"Central Warehouse-Security",
	"Feni CSP-IT & Network",
	"Tangail-Sales",
	"Mymensingh CSP-Printer",
	"E.Road-Sales",
	"IT Support",
	"Mymensingh CSP-Support Staff",
	"Gazipur CSP-Repair",
	"Narayangonj-Security",
	"Rangpur CSP-IT & Network",
	"HO-Cleaner",
	"EISL-Support Staff",
	"Production",
	"Central Warehouse-Cook",
	"HO-Electritian",
	"Quality Control",
	"Rajshahi CSP-Support Staff",
	"Narayanganj-Sales",
	"Gazipur-Sales",
	"Narayanganj-Security",
	"Gulistan-Accounts",
	"CCSP-Lenovo",
	"Sylhet CSP-Support Engineering",
	"Transport",
	"IDB CSP-Repair",
	"Tender Sales",
	"Support - Corp.",
	"Accounts - Corp.",
	"Security & Surveillance",
	"Unified Communication",
	"Software Development",
	"Product Management & Pre Sales",
	"Direct Sales",
	"Corporate Pre-Sales",
	"Printing Solution",
	"ERP Operations",
	"Engineering Coordinator",
	"Networks & Cyber Security",
	"Sales Admin",
	"Network & Security Surveillance",
	"Project Management",
	"Network & Cyber Security",
	"Team IT",
  ];
  
  const Excel_Section = new Map();
  
  excel_sections.forEach((option) => {
	Excel_Section.set("")
	Excel_Section.set(option, { value: option, label: __(option) });
  });
  
  const Excel_section_option = Array.from(Excel_Section.values());
  
  // set_options for excel_subsection
  const excel_sub_section = [
	"HO-Sales",
	"HiK Vision",
	"IDB-Sales",
	"Multiplan-Sales",
	"Treasury",
	"Digital-X & Logitech",
	"Zone Sales-2",
	"HO-Accounts",
	"Credit Management",
	"Multiplan-Inventory",
	"Uttara-Sales",
	"Zone Sales-1",
	"RMA-Return Material Authorization",
	"Lenovo",
	"IDB CSP-Inventory",
	"TP-Link-Technical",
	"Technical",
	"Repair",
	"PQC",
	"OQC",
	"Multiplan-Support Staff",
	"Micropack & XP-PEN",
	"Logitech, DigitalX Speaker",
	"Logitech",
	"ISP-Sales",
	"IQC",
	"HikStorage & DigitalX UPS",
	"DigitalX Speaker",
	"CSP-Khulna",
	"CSP-Courier Section",
	"Central Warehouse-VAT & Tax",
	"Central Warehouse-Transport",
	"CCSP-RMA Inventory",
	"CCSP-Office Support",
	"CCSP-Local RMA",
	"CCSP-Foreign RMA",
	"Baridhara Pr.",
	"Assembly",
	"Fire & Engineering",
	"Billing - Printing",
	"RMA Carrier",
	"Printing Division",
	"Billing - Sales",
	"Grandstream / Avar",
	"Warehouse - Logistics",
	"Active Network/Cyber Security (Cisco, Juniper, Sophos)",
	"EPSON / Lenovo",
	"Passive Network (Rosenberger / Commscope)",
	"Corp. - CRC",
	"KYOCERA",
  ];
  
  const excel_sub_section_map = new Map();
  
  excel_sub_section.forEach((option) => {
	excel_sub_section_map.set("")
	excel_sub_section_map.set(option, { value: option, label: __(option) });
  });
  
  const excelSubSectionOPtion = Array.from(excel_sub_section_map.values());
  
  // excel job location
  
  const job_location = [
	"Head Office",
	"Corporate Office",
	"Dhanmondi Warehouse",
	"IDB",
	"Multiplan",
	"CCSP-Multiplan",
	"Uttara",
	"Motijheel Zone",
	"CSP-Motijheel",
	"CSP-Gulistan",
	"Gulistan Zone",
	"CTG",
	"CSP-Uttara",
	"Khulna Zone",
	"Bogura Zone",
	"Dhanmondi Zone",
	"Sylhet Zone",
	"CSP-Bogura",
	"Rangpur Zone",
	"CSP-CTG",
	"Faridpur Zone",
	"Rajshahi Zone",
	"Mymensingh Zone",
	"Feni Zone",
	"CSP-Rangpur",
	"Barishal Zone",
	"CSP-Sylhet",
	"CSP-Khulna",
	"CSP-IDB",
	"Kusthia Zone",
	"Savar Zone",
	"Gazipur Zone",
	"CSP-Rajshahi",
	"Dinajpur Zone",
	"Noakhali Zone",
	"Narayanganj Zone",
	"Pabna Zone",
	"CSP-Feni",
	"Tangail Zone",
	"CSP-Mymensingh",
	"E. Road Zone",
	"CSP-Gazipur",
	"CTG Corporate",
	"CTG Zone",
	"Bangabandhu Hi-Tech City",
	"Bogra Zone",
  ];
  
  const excel_job_location = new Map();
  
  excel_sub_section.forEach((option) => {
	excel_job_location.set("")
	excel_job_location.set(option, { value: option, label: __(option) });
  });
  
  const excelJobOPtion = Array.from(excel_job_location.values());
  frappe.query_reports["Excel Monthly Attendance Sheet"] = {
	filters: [
	  // {
	  //     "fieldname": "month",
	  //     "label": __("Month"),
	  //     "fieldtype": "Select",
	  //     "reqd": 1,
	  //     "excel_sub_section": [
	  //         { "value": 1, "label": __("Jan") },
	  //         { "value": 2, "label": __("Feb") },
	  //         { "value": 3, "label": __("Mar") },
	  //         { "value": 4, "label": __("Apr") },
	  //         { "value": 5, "label": __("May") },
	  //         { "value": 6, "label": __("June") },
	  //         { "value": 7, "label": __("July") },
	  //         { "value": 8, "label": __("Aug") },
	  //         { "value": 9, "label": __("Sep") },
	  //         { "value": 10, "label": __("Oct") },
	  //         { "value": 11, "label": __("Nov") },
	  //         { "value": 12, "label": __("Dec") },
	  //     ],
	  //     "default": frappe.datetime.str_to_obj(frappe.datetime.get_today()).getMonth() + 1,
	  // 	"onchange": function() {
	  // 		console.log(frappe)
	  // 	}
  
	  // },
  
	  // {
	  //     "fieldname": "year",
	  //     "label": __("Year"),
	  //     "fieldtype": "Select",
	  //     "reqd": 1,
  
	  // },
	  {
		fieldname: "date_range",
		label: __("Date Range"),
		fieldtype: "Date Range",
		reqd: 1,
		default: [frappe.datetime.month_start(), frappe.datetime.month_end()],
	  },
  
	  ,
	  // {
	  // 	"fieldname": "start_date",
	  // 	"label": __("Start Date"),
	  // 	"fieldtype": "Date",
	  // 	"default":frappe.datetime.month_start()
  
	  // },
	  // {
	  // 	"fieldname": "end_date",
	  // 	"label": __("End Date"),
	  // 	"fieldtype": "Date",
	  // 	"default":frappe.datetime.month_end()
  
	  // },
  
	  {
		fieldname: "company",
		label: __("Company"),
		fieldtype: "Link",
		options: "Company",
		default: frappe.defaults.get_user_default("Company"),
		reqd: 1,
	  },
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
		fieldtype: "Select",
		options: [
			"",
		  { value: "Corporate Sales", label: __("Corporate Sales") },
		  { value: "Finance & Accounts", label: __("Finance & Accounts") },
		  {
			value: "Engineering & Technology",
			label: __("Engineering & Technology"),
		  },
		  { value: "Digital Marketing", label: __("Digital Marketing") },
		  {
			value: "Enterprise Product Management",
			label: __("Enterprise Product Management"),
		  },
		  { value: "Management", label: __("Management") },
		  { value: "Operations", label: __("Operations") },
		  { value: "Inventory Management", label: __("Inventory Management") },
		  { value: "Sales", label: __("Sales") },
		  {
			value: "Customer Service Point",
			label: __("Customer Service Point"),
		  },
		  { value: "Product Management", label: __("Product Management") },
		  { value: "Human Resources", label: __("Human Resources") },
		  { value: "Marketing", label: __("Marketing") },
		  { value: "Factory Operations", label: __("Factory Operations") },
		  { value: "Production Control", label: __("Production Control") },
		  { value: "Material Management", label: __("Material Management") },
		  { value: "Production Management", label: __("Production Management") },
		  {
			value: "Equipment & Maintenance",
			label: __("Equipment & Maintenance"),
		  },
		],
	  },
	  {
		fieldname: "excel_section",
		label: __("Section"),
		fieldtype: "Select",
		options: Excel_section_option,
	  },
  
	  {
		fieldname: "excel_sub_section",
		label: __("Sub Section"),
		fieldtype: "Select",
		options: excelSubSectionOPtion,
	  },
	  {
		fieldname: "excel_job_location",
		label: __("Excel Job Location"),
		fieldtype: "Select",
		options: excelJobOPtion,
	  },
	  // {
	  // 	"fieldname":"group_by",
	  // 	"label": __("Group By"),
	  // 	"fieldtype": "Select",
	  // 	"excel_sub_section": ["","Branch","Grade","Department","Designation"]
	  // },
	  {
		fieldname: "summarized_view",
		label: __("Summarized View"),
		fieldtype: "Check",
		Default: 0,
	  },
	],
	onload: function () {
	  return frappe.call({
		method:
		  "hrms.hr.report.monthly_attendance_sheet.monthly_attendance_sheet.get_attendance_years",
		callback: function (r) {
		  var year_filter = frappe.query_report.get_filter("year");
		  year_filter.df.excel_sub_section = r.message;
		  year_filter.df.default = r.message.split("\n")[0];
		  year_filter.refresh();
		  year_filter.set_input(year_filter.df.default);
		},
	  });
	},
	formatter: function (value, row, column, data, default_formatter) {
	  value = default_formatter(value, row, column, data);
	  const summarized_view =
		frappe.query_report.get_filter_value("summarized_view");
	  const group_by = frappe.query_report.get_filter_value("group_by");
  
	  if (!summarized_view) {
		if (
		  (group_by && column.colIndex > 3) ||
		  (!group_by && column.colIndex > 2)
		) {
		  if (value == "P" || value == "WFH")
			value = "<span style='color:green'>" + value + "</span>";
		  else if (value == "A")
			value = "<span style='color:red'>" + value + "</span>";
		  else if (value == "HD")
			value = "<span style='color:orange'>" + value + "</span>";
		  else if (value == "L")
			value = "<span style='color:#318AD8'>" + value + "</span>";
		}
	  }
  
	  return value;
	},
  };
  