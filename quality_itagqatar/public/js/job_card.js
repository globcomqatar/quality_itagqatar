const INSPECTION_FORMS_PROMISE = frappe.call({
	method: 'quality_itagqatar.quality_itag_qatar.api.shared.get_inspection_forms',
	no_spinner: true,
}).then((r) => r.message || []);


frappe.ui.form.on('Job Card', {
	onload(frm) {
		INSPECTION_FORMS_PROMISE.then((forms) => apply_inspection_form_options(frm, forms));
	},

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


function apply_inspection_form_options(frm, forms) {
	if (!forms.length) return;
	const options = ['', ...forms].join('\n');
	frm.set_df_property('custom_inspection_form', 'options', options);
	if (frm.fields_dict.custom_inspection_form) {
		frm.fields_dict.custom_inspection_form.df.options = options;
	}
	frm.refresh_field('custom_inspection_form');
}
