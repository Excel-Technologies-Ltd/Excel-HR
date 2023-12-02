
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
		read_only: 1,
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
		fieldname:'department',
		label: __('Department'),
		fieldtype: 'Link',
		options: 'Department',
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
		options: [
			"",
			{ value: 'HO-Sales', label:__( 'HO-Sales' )},
			{ value: 'HiK Vision', label:__( 'HiK Vision' )},
			{ value: 'IDB-Sales', label:__( 'IDB-Sales' )},
			{ value: 'Multiplan-Sales', label:__( 'Multiplan-Sales' )},
			{ value: 'Treasury', label:__( 'Treasury' )},
			{ value: 'Digital-X & Logitech', label:__( 'Digital-X & Logitech' )},
			{ value: 'Zone Sales-2', label:__( 'Zone Sales-2' )},
			{ value: 'HO-Accounts', label:__( 'HO-Accounts' )},
			{ value: 'Credit Management', label:__( 'Credit Management' )},
			{ value: 'Multiplan-Inventory', label:__( 'Multiplan-Inventory' )},
			{ value: 'Uttara-Sales', label:__( 'Uttara-Sales' )},
			{ value: 'Zone Sales-1', label:__( 'Zone Sales-1' )},
			{
			  value: 'RMA-Return Material Authorization',
			  label:__( 'RMA-Return Material Authorization')
			},
			{ value: 'Lenovo', label:__( 'Lenovo') },
			{ value: 'IDB CSP-Inventory', label:__ ('IDB CSP-Inventory') },
			{ value: 'TP-Link', label:__( 'TP-Link') },{
				value: 'CCSP-Support Engineering',
				label:__( 'CCSP-Support Engineering')
			  },
			  {
				value: 'Central Warehouse-Driver',
				label:__( 'Central Warehouse-Driver')
			  },
			  { value: 'CCSP-Repair', label:__( 'CCSP-Repair') },
			  { value: 'Motijheel-Sales', label:__( 'Motijheel-Sales') },
			  { value: 'HO-Support Staff', label:__( 'HO-Support Staff') },
			  { value: 'HO-Driver', label:__( 'HO-Driver') },
			  { value: 'CCSP-IT & Network', label:__( 'CCSP-IT & Network') },
			  { value: 'Zone Sales-3', label:__( 'Zone Sales-3') },
			  { value: 'Motijheel CSP-Printer', label:__( 'Motijheel CSP-Printer') },
			  {
				value: 'Gulistan CSP-Support Staff',
				label:__( 'Gulistan CSP-Support Staff')
			  },
			  { value: 'Administration', label:__( 'Administration') },
			  {
				value: 'HO-Delivery & Collection',
				label:__( 'HO-Delivery & Collection')
			  },
			  { value: 'Gulistan-Sales', label:__( 'Gulistan-Sales') },
			  { value: 'CTG-Sales', label:__( 'CTG-Sales') },
			  { value: 'CCSP-Support Staff', label:__( 'CCSP-Support Staff') },
			  { value: 'Uttara CSP-Repair', label:__( 'Uttara CSP-Repair') },
			  { value: 'Khulna-Sales', label:__( 'Khulna-Sales') },
			  { value: 'Bogura-Sales', label:__( 'Bogura-Sales') },
			  { value: 'Dhanmondi-Sales', label:__( 'Dhanmondi-Sales') },
			  { value: 'Sylhet-Sales', label:__( 'Sylhet-Sales') },
			  { value: 'Inventory Audit', label:__( 'Inventory Audit') },
			  { value: 'Gulistan CSP-Repair', label:__( 'Gulistan CSP-Repair') },
			  { value: 'VAT & Tax', label:__( 'VAT & Tax') },
			  { value: 'Inventory Management', label:__( 'Inventory Management') },
			  {
				value: 'Bogura CSP-IT & Network',
				label:__( 'Bogura CSP-IT & Network')
			  },
			  { value: 'Rangpur-Sales', label:__( 'Rangpur-Sales') },
			  { value: 'HO-Front Desk', label:__( 'HO-Front Desk') },
			  { value: 'CTG CSP-Printer', label:__( 'CTG CSP-Printer') },
			  { value: 'Epson', label:__( 'Epson') },
			  { value: 'Faridpur-Sales', label:__( 'Faridpur-Sales') },
			  { value: 'CCSP-Printer', label:__( 'CCSP-Printer') },
			  { value: 'Uttara-Accounts', label:__( 'Uttara-Accounts') },
			  { value: 'Rajshahi-Sales', label:__( 'Rajshahi-Sales') },
			  {
				value: 'CTG-Delivery & Collection',
				label:__( 'CTG-Delivery & Collection')
			  },
			  { value: 'Mymensingh-Sales', label:__( 'Mymensingh-Sales') },
			  { value: 'Feni-Sales', label:__( 'Feni-Sales') },
			  {
				value: 'Rangpur CSP-Support Staff',
				label:__( 'Rangpur CSP-Support Staff')
			  },
			  { value: 'Barishal-Sales', label:__( 'Barishal-Sales') },
			  {
				value: 'Bogura CSP-Support Staff',
				label:__( 'Bogura CSP-Support Staff')
			  },
			  { value: 'New Frontier', label:__( 'New Frontier') },
			  {
				value: 'Sylhet CSP-Support Staff',
				label:__( 'Sylhet CSP-Support Staff')
			  },
			  { value: 'Khulna CSP-Repair', label:__( 'Khulna CSP-Repair') },
			  { value: 'SI-Sales', label:__( 'SI-Sales') },
			  { value: 'MD’s Secretariat', label:__( 'MD’s Secretariat') },
			  { value: 'IDB CSP-Support Staff', label:__( 'IDB CSP-Support Staff') },
			  {
				value: 'Motijheel CSP-Support Staff',
				label:__( 'Motijheel CSP-Support Staff')
			  },
			  {
				value: 'Central Warehouse-Billing',
				label:__( 'Central Warehouse-Billing')
			  },
			  { value: 'CTG-Accounts', label:__( 'CTG-Accounts') },
			  { value: 'IDB-Inventory', label:__( 'IDB-Inventory') },
			  { value: 'Multipan-Accounts', label:__( 'Multipan-Accounts') },
			  { value: 'Kusthia-Sales', label:__( 'Kusthia-Sales') },
			  { value: 'Zone Sales-4', label:__( 'Zone Sales-4') },
			  { value: 'Savar-Sales', label:__( 'Savar-Sales') },
			  { value: 'IDB CSP-Printer', label:__( 'IDB CSP-Printer') },
			  { value: 'FTTx', label:__( 'FTTx') },
			  { value: 'Uttara-Inventory', label:__( 'Uttara-Inventory') },
			  { value: 'CTG-Support Staff', label:__( 'CTG-Support Staff') },
			  { value: 'Multiplan Sales', label:__( 'Multiplan Sales') },
			  {
				value: 'Rajshahi CSP-Support Engineering',
				label:__( 'Rajshahi CSP-Support Engineering')
			  },
			  {
				value: 'Supply Chain Management',
				label:__( 'Supply Chain Management')
			  },
			  { value: 'HO-Cook', label:__( 'HO-Cook') },
			  {
				value: 'Central Warehouse-Cleaner',
				label:__( 'Central Warehouse-Cleaner')
			  },
			  { value: 'Dinajpur-Sales', label:__( 'Dinajpur-Sales') },
			  { value: 'CTG-Driver', label:__( 'CTG-Driver') },
			  {
				value: 'Khulna CSP-Support Staff',
				label:__( 'Khulna CSP-Support Staff')
			  },
			  { value: 'Motijheel CSP-Accounts', label:__( 'Motijheel CSP-Accounts') },
			  {
				value: 'Central Warehouse-Accounts',
				label:__( 'Central Warehouse-Accounts')
			  },
			  { value: 'Project', label:__( 'Project') },
			  { value: 'IDB-Accounts', label:__( 'IDB-Accounts') },
			  { value: 'MIS', label:__( 'MIS') },
			  { value: 'Pabna-Sales', label:__( 'Pabna-Sales') },
			  {
				value: 'Central Warehouse-Security',
				label:__( 'Central Warehouse-Security')
			  },
			  { value: 'Feni CSP-IT & Network', label:__( 'Feni CSP-IT & Network') },
			  { value: 'Tangail-Sales', label:__( 'Tangail-Sales') },
			  { value: 'Mymensingh CSP-Printer', label:__( 'Mymensingh CSP-Printer') },
			  { value: 'E.Road-Sales', label:__( 'E.Road-Sales' )},
			  { value: 'IT Support', label:__( 'IT Support' )},
			  {
				value: 'Mymensingh CSP-Support Staff',
				label:__( 'Mymensingh CSP-Support Staff')
			  },
			  { value: 'Gazipur CSP-Repair', label:__( 'Gazipur CSP-Repair' )},
			  { value: 'Narayangonj-Security', label:__( 'Narayangonj-Security' )},
			  {
				value: 'Rangpur CSP-IT & Network',
				label:__( 'Rangpur CSP-IT & Network')
			  },
			  { value: 'HO-Cleaner', label:__( 'HO-Cleaner' )},
			  { value: 'EISL-Support Staff', label:__( 'EISL-Support Staff' )},
			  { value: 'Production', label:__( 'Production' )},
			  { value: 'Central Warehouse-Cook', label:__( 'Central Warehouse-Cook' )},
			  { value: 'HO-Electritian', label:__( 'HO-Electritian' )},
			  { value: 'Quality Control', label:__( 'Quality Control' )},
			  {
				value: 'Rajshahi CSP-Support Staff',
				label:__( 'Rajshahi CSP-Support Staff')
			  },
			  { value: 'Narayanganj-Sales', label:__( 'Narayanganj-Sales' )},
			  { value: 'Gazipur-Sales', label:__( 'Gazipur-Sales' )},
			  { value: 'Narayanganj-Security', label:__( 'Narayanganj-Security' )},
			  { value: 'Gulistan-Accounts', label:__( 'Gulistan-Accounts' )},
			  { value: 'CCSP-Lenovo', label:__( 'CCSP-Lenovo' )},
			  {
				value: 'Sylhet CSP-Support Engineering',
				label:__( 'Sylhet CSP-Support Engineering')
			  },
			  { value: 'Transport', label:__( 'Transport' )},
			  { value: 'IDB CSP-Repair', label:__( 'IDB CSP-Repair' )},
			  { value: 'Tender Sales', label:__( 'Tender Sales' )},
			  { value: 'Support - Corp.', label:__( 'Support - Corp.' )},
			  { value: 'Accounts - Corp.', label:__( 'Accounts - Corp.' )},
			  {
				value: 'Security & Surveillance',
				label:__( 'Security & Surveillance')
			  },
			  { value: 'Unified Communication', label:__( 'Unified Communication' )},
			  { value: 'Software Development', label:__( 'Software Development' )},
			  {
				value: 'Product Management & Pre Sales',
				label:__( 'Product Management & Pre Sales')
			  },
			  { value: 'Direct Sales', label:__( 'Direct Sales' )},
			  { value: 'Corporate Pre-Sales', label:__( 'Corporate Pre-Sales' )},
			  { value: 'Printing Solution', label:__( 'Printing Solution' )},
			  { value: 'ERP Operations', label:__( 'ERP Operations' )},
			  {
				value: 'Engineering Coordinator',
				label:__( 'Engineering Coordinator')
			  },
			  {
				value: 'Networks & Cyber Security',
				label:__( 'Networks & Cyber Security')
			  },
			  { value: 'Sales Admin', label:__( 'Sales Admin' )},
			  {
				value: 'Network & Security Surveillance',
				label:__( 'Network & Security Surveillance')
			  },
			  { value: 'Project Management', label:__( 'Project Management' )},
			  {
				value: 'Network & Cyber Security',
				label:__( 'Network & Cyber Security')
			  },
			  { value: 'Team IT', label:__( 'Team IT' )},
			  { value: 'EISL-Accounts', label:__( 'EISL-Accounts') }

			//   hgvjg
			  
		]
	  },
	  {
		fieldname: "excel_sub_section",
		label:__("Sub Section"),
		fieldtype: "Select",
		options: [
			"",
			{ value: 'HO-Sales', label:__( 'HO-Sales') },
  { value: 'HiK Vision', label:__( 'HiK Vision') },
  { value: 'IDB-Sales', label:__( 'IDB-Sales') },
  { value: 'Multiplan-Sales', label:__( 'Multiplan-Sales') },
  { value: 'Treasury', label:__( 'Treasury') },
  { value: 'Digital-X & Logitech', label:__( 'Digital-X & Logitech') },
  { value: 'Zone Sales-2', label:__( 'Zone Sales-2') },
  { value: 'HO-Accounts', label:__( 'HO-Accounts') },
  { value: 'Credit Management', label:__( 'Credit Management') },
  { value: 'Multiplan-Inventory', label:__( 'Multiplan-Inventory') },
  { value: 'Uttara-Sales', label:__( 'Uttara-Sales') },
  { value: 'Zone Sales-1', label:__( 'Zone Sales-1') },
  {
    value: 'RMA-Return Material Authorization',
    label:__( 'RMA-Return Material Authorization')
  },
  { value: 'Lenovo', label:__( 'Lenovo') },
  { value: 'IDB CSP-Inventory', label:__( 'IDB CSP-Inventory') },
  { value: 'TP-Link-Technical', label:__( 'TP-Link-Technical') },
  { value: 'Technical', label:__( 'Technical') },
  { value: 'Repair', label:__( 'Repair') },
  { value: 'PQC', label:__( 'PQC') },
  { value: 'OQC', label:__( 'OQC') },
  {
    value: 'Multiplan-Support Staff',
    label:__( 'Multiplan-Support Staff')
  },
  { value: 'Micropack & XP-PEN', label:__( 'Micropack & XP-PEN') },
  {
    value: 'Logitech, DigitalX Speaker',
    label:__( 'Logitech, DigitalX Speaker')
  },
  { value: 'Logitech', label:__( 'Logitech') },
  { value: 'ISP-Sales', label:__( 'ISP-Sales') },
  { value: 'IQC', label:__( 'IQC') },
  {
    value: 'HikStorage & DigitalX UPS',
    label:__( 'HikStorage & DigitalX UPS')
  },
  { value: 'DigitalX Speaker', label:__( 'DigitalX Speaker') },
  { value: 'CSP-Khulna', label:__( 'CSP-Khulna') },
  { value: 'CSP-Courier Section', label:__( 'CSP-Courier Section') },
  {
    value: 'Central Warehouse-VAT & Tax',
    label:__( 'Central Warehouse-VAT & Tax')
  },
  {
    value: 'Central Warehouse-Transport',
    label:__( 'Central Warehouse-Transport')
  },
  { value: 'CCSP-RMA Inventory', label:__( 'CCSP-RMA Inventory') },
  { value: 'CCSP-Office Support', label:__( 'CCSP-Office Support') },
  { value: 'CCSP-Local RMA', label:__( 'CCSP-Local RMA') },
  { value: 'CCSP-Foreign RMA', label:__( 'CCSP-Foreign RMA') },
  { value: 'Baridhara Pr.', label:__( 'Baridhara Pr.') },
  { value: 'Assembly', label:__( 'Assembly') },
  { value: 'Fire & Engineering', label:__( 'Fire & Engineering') },
  { value: 'Billing - Printing', label:__( 'Billing - Printing') },
  { value: 'RMA Carrier', label:__( 'RMA Carrier') },
  { value: 'Printing Division', label:__( 'Printing Division') },
  { value: 'Billing - Sales', label:__( 'Billing - Sales') },
  { value: 'Grandstream / Avar', label:__( 'Grandstream / Avar') },
  { value: 'Warehouse - Logistics', label:__( 'Warehouse - Logistics') },
  {
    value: 'Active Network/Cyber Security (Cisco, Juniper, Sophos)',
    label:__( 'Active Network/Cyber Security (Cisco, Juniper, Sophos')
  },
  { value: 'EPSON / Lenovo', label:__( 'EPSON / Lenovo') },
  {
    value: 'Passive Network (Rosenberger / Commscope)',
    label:__( 'Passive Network (Rosenberger / Commscope')
  },
  { value: 'Corp. - CRC', label:__( 'Corp. - CRC') },
  { value: 'KYOCERA', label:__( 'KYOCERA' )}
		]
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
		{ value: 'Bogra Zone', label:__( 'Bogra Zone') }
	],
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
  