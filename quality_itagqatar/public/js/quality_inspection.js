// Inward Serial No dropdown — populates from linked Stock Entry / Job Card.
frappe.ui.form.on('Quality Inspection', {
	onload(frm) {
		populate_serial_numbers(frm);
	},
	reference_type(frm) {
		populate_serial_numbers(frm);
	},
	reference_name(frm) {
		populate_serial_numbers(frm);
	},
	item_code(frm) {
		populate_serial_numbers(frm);
	},
});


function populate_serial_numbers(frm) {
	if (frm.doc.reference_type === 'Stock Entry' && frm.doc.reference_name) {
		populate_serial_numbers_from_stock_entry(frm);
	} else if (frm.doc.reference_type === 'Job Card' && frm.doc.reference_name) {
		populate_serial_numbers_from_job_card(frm);
	} else {
		frm.set_df_property('custom_inward_serial_no', 'options', '');
	}
}


function populate_serial_numbers_from_stock_entry(frm) {
	if (!frm.doc.item_code) {
		frm.set_df_property('custom_inward_serial_no', 'options', '');
		return;
	}
	frappe.call({
		method: 'frappe.client.get',
		args: { doctype: 'Stock Entry', name: frm.doc.reference_name },
		callback(r) {
			if (!(r.message && r.message.items)) return;
			const matching_item = r.message.items.find((item) => item.item_code === frm.doc.item_code);
			if (!(matching_item && matching_item.serial_no)) {
				frm.set_df_property('custom_inward_serial_no', 'options', '');
				return;
			}
			const serial_numbers = matching_item.serial_no
				.split('\n')
				.map((s) => s.trim())
				.filter((s) => s.length > 0);
			apply_serial_options(frm, serial_numbers, __('Stock Entry'));
		},
	});
}


function populate_serial_numbers_from_job_card(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: { doctype: 'Job Card', name: frm.doc.reference_name },
		callback(r) {
			if (!r.message) return;
			const job_card = r.message;
			let serial_numbers = [];
			if (job_card.custom_work_order_serial_no) {
				serial_numbers = job_card.custom_work_order_serial_no
					.split('\n')
					.map((s) => s.trim())
					.filter((s) => s.length > 0);
			}
			if (serial_numbers.length === 0) {
				serial_numbers = get_serial_numbers_from_time_logs(job_card);
			}
			apply_serial_options(frm, serial_numbers, __('Job Card'));
		},
	});
}


function apply_serial_options(frm, serial_numbers, source_label) {
	if (serial_numbers.length === 0) {
		frm.set_df_property('custom_inward_serial_no', 'options', '');
		return;
	}
	frm.set_df_property('custom_inward_serial_no', 'options', serial_numbers.join('\n'));
	if (serial_numbers.length === 1 && !frm.doc.custom_inward_serial_no) {
		frm.doc.custom_inward_serial_no = serial_numbers[0];
		frm.refresh_field('custom_inward_serial_no');
		frappe.show_alert({
			message: __('Serial number auto-selected: {0}', [serial_numbers[0]]),
			indicator: 'blue',
		}, 3);
	} else {
		frappe.show_alert({
			message: __('Serial numbers loaded from {0}: {1}', [source_label, serial_numbers.length]),
			indicator: 'green',
		}, 3);
	}
}


function get_serial_numbers_from_time_logs(job_card) {
	if (!job_card.time_logs || job_card.time_logs.length === 0) return [];
	const serial_set = new Set();
	for (const log of job_card.time_logs) {
		if (!log.custom_serial_no) continue;
		log.custom_serial_no
			.split('\n')
			.map((s) => s.trim())
			.filter((s) => s.length > 0)
			.forEach((s) => serial_set.add(s));
	}
	return Array.from(serial_set);
}
