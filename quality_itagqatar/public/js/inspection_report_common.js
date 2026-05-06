const INSPECTION_REPORT_DOCTYPES = [
	'Assembly Traceability Record',
	'Certificate of Conformity',
	'Contract Review Record',
	'Dimensional Inspection Report',
	'Final Machining Visual Examination Report',
	'QC Material Release Note',
	'Visual Examination Report',
];

INSPECTION_REPORT_DOCTYPES.forEach(function (doctype) {
	frappe.ui.form.on(doctype, {
		on_submit(frm) {
			if (!frm.doc.quality_inspection) return;

			frappe.db.get_value(
				'Quality Inspection',
				frm.doc.quality_inspection,
				['reference_type', 'reference_name'],
				function (qi) {
					if (qi && qi.reference_type === 'Job Card' && qi.reference_name) {
						frappe.show_alert({
							message: __('Returning to Job Card {0}', [qi.reference_name]),
							indicator: 'green',
						}, 3);
						frappe.model.clear_doc('Job Card', qi.reference_name);
						frappe.set_route('Form', 'Job Card', qi.reference_name);
					} else {
						frappe.show_alert({
							message: __('Returning to Quality Inspection {0}', [frm.doc.quality_inspection]),
							indicator: 'green',
						}, 3);
						frappe.set_route('Form', 'Quality Inspection', frm.doc.quality_inspection);
					}
				}
			);
		},
	});
});
