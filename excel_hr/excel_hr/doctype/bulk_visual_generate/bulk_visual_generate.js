// Copyright (c) 2025, Shaid Azmin and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Visual Generate', {
	refresh: function(frm) {
    //   add custom button to generate banners from array
    console.log(frm.doc.customer_list);
    console.log(frm)
    if(!frm.is_new() && frm.doc.customer_list.length > 0) {
		frm.add_custom_button(__('Generate Visuals'), function() {
			generate_banners_from_array(frm);
		});
	}
	}
});



function generate_banners_from_array(frm) {
    let customers_data = frm.doc.customer_list;
	console.log(customers_data);

    frappe.show_alert({
        message: __('Generating banners for {0} customers...', [customers_data.length]),
        indicator: 'blue'
    });

    frappe.call({
        method: 'excel_hr.excel_hr.doctype.bulk_visual_generate.bulk_visual_generate.generate_bulk_banners',
        args: {
            customers_data: frm.doc.customer_list,
            base_image_path: frm.doc.attach_image  ,
            font_style: frm.doc.font_style
        },
        freeze: true,
        freeze_message: __('Generating Banners...'),
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Successfully generated {0} banners!', [r.message.total_customers]),
                    indicator: 'green'
                }, 5);

                // Show download dialog
                frappe.msgprint({
                    title: __('Banners Generated Successfully'),
                    message: __('Total banners: {0}<br>File: {1}', [r.message.total_customers, r.message.file_name]),
                    primary_action: {
                        label: __('Download ZIP'),
                        action: function() {
                            window.open(r.message.file_url, '_blank');
                        }
                    }
                });
            } else {
                frappe.msgprint({
                    title: __('Error'),
                    message: r.message.message || __('Failed to generate banners'),
                    indicator: 'red'
                });
            }
        },
        error: function(err) {
            frappe.msgprint({
                title: __('Error'),
                message: __('An error occurred while generating banners'),
                indicator: 'red'
            });
        }
    });
}
