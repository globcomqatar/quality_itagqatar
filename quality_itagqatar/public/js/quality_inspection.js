frappe.ui.form.on('Quality Inspection', {
	custom_inspection_form(frm) {
		if (frm.doc.docstatus !== 0) return;
		if (!frm.doc.custom_inspection_form) return;
		if (!frm.is_dirty()) return;
		frm.save();
	},
});
