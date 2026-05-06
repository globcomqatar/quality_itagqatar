frappe.ui.form.on('Job Card', {
	custom_start_inspection(frm) {
		if (!frm.doc.custom_inspection_form) {
			frappe.msgprint(__('Please select an Inspection Form first.'));
			return;
		}

		frappe.call({
			method: 'quality_itagqatar.quality_itag_qatar.api.job_card.start_jc_inspection',
			args: {
				job_card: frm.doc.name,
				inspection_form: frm.doc.custom_inspection_form,
			},
			freeze: true,
			freeze_message: __('Creating inspection report...'),
			callback(r) {
				if (r.message) {
					frappe.set_route('Form', r.message.doctype, r.message.name);
				}
			},
		});
	},
});
