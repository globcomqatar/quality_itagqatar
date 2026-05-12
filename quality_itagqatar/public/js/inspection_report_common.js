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
		refresh(frm) {
			if (frm.is_new() || frm.doc.docstatus !== 0) return;
			frm.add_custom_button(
				__('Refresh from Source'),
				function () {
					frappe.call({
						method: 'quality_itagqatar.quality_itag_qatar.inspection.prefill.refresh_from_source',
						args: { doctype: frm.doc.doctype, name: frm.doc.name },
						freeze: true,
						freeze_message: __('Refreshing from Job Card chain…'),
					}).then(function (r) {
						const count = Object.keys((r.message && r.message.filled) || {}).length;
						frappe.show_alert({
							message: count
								? __('Filled {0} field(s) from source', [count])
								: __('Nothing to fill — clear a field first to force a refresh'),
							indicator: count ? 'green' : 'blue',
						});
						frm.reload_doc();
					});
				},
				__('Actions')
			);
		},
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
