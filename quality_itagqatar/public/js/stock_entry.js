const INSPECTION_FORMS_PROMISE = frappe.call({
	method: 'quality_itagqatar.quality_itag_qatar.api.shared.get_inspection_forms',
	no_spinner: true,
}).then((r) => r.message || []);


frappe.ui.form.on('Stock Entry', {
	onload(frm) {
		INSPECTION_FORMS_PROMISE.then((forms) => apply_inspection_form_options(frm, forms));
	},

	refresh(frm) {
		frm.toggle_display('custom_start_inspection', frm.doc.docstatus === 0);
	},

	custom_start_inspection(frm) {
		if (frm.doc.docstatus !== 0) return;
		if (!frm.doc.custom_inspection_form) {
			frappe.msgprint(__('Please select an Inspection Form first.'));
			return;
		}
		if (!frm.doc.items || frm.doc.items.length === 0) {
			frappe.msgprint(__('Please add items to the Stock Entry before starting inspection.'));
			return;
		}
		if (frm.doc.custom_subcontracted_job == 1) {
			const first_item = frm.doc.items[0];
			const has_serial = first_item.serial_no || first_item.serial_and_batch_bundle;
			if (!has_serial) {
				frappe.msgprint({
					title: __('Serial Numbers Required'),
					message: __('Serial numbers must be entered in the first item row before starting inspection for subcontracted jobs.'),
					indicator: 'red',
				});
				return;
			}
		}

		if (frm.doc.items.length === 1) {
			start_inspection(frm, frm.doc.items[0].name);
			return;
		}
		open_row_picker(frm);
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


function open_row_picker(frm) {
	const rows = frm.doc.items;
	const radio_html = rows
		.map((row, i) => {
			const sn = row.serial_no ? ` &middot; SN ${frappe.utils.escape_html(row.serial_no)}` : '';
			const bn = row.batch_no ? ` &middot; Batch ${frappe.utils.escape_html(row.batch_no)}` : '';
			const label = `${row.idx}. ${frappe.utils.escape_html(row.item_code)} &mdash; Qty ${row.qty}${sn}${bn}`;
			return `<label class="d-block py-1"><input type="radio" name="se_inspect_row" value="${frappe.utils.escape_html(row.name)}"${i === 0 ? ' checked' : ''}> ${label}</label>`;
		})
		.join('');

	const d = new frappe.ui.Dialog({
		title: __('Select Item Row to Inspect'),
		fields: [
			{
				fieldname: 'row_picker',
				fieldtype: 'HTML',
				options: `<div class="se-inspect-row-picker">${radio_html}</div>`,
			},
		],
		primary_action_label: __('Start Inspection'),
		primary_action() {
			const selected = d.$wrapper.find('input[name="se_inspect_row"]:checked').val();
			if (!selected) {
				frappe.msgprint(__('Please select an item row.'));
				return;
			}
			d.hide();
			start_inspection(frm, selected);
		},
	});
	d.show();
}


function start_inspection(frm, child_row_reference) {
	frappe.call({
		method: 'quality_itagqatar.quality_itag_qatar.api.stock_entry.start_se_inspection',
		args: {
			stock_entry: frm.doc.name,
			inspection_form: frm.doc.custom_inspection_form,
			child_row_reference,
		},
		freeze: true,
		freeze_message: __('Creating inspection report...'),
		callback(r) {
			if (r.message) {
				frappe.set_route('Form', r.message.doctype, r.message.name);
			}
		},
	});
}
