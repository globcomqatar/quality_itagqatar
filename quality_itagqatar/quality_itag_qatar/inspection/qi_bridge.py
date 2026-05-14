import frappe
from frappe import _


def create_and_submit_qi(jc, inspection_form):
    """Create and submit a Quality Inspection silently for a Job Card.

    ERPNext requires a submitted QI linked to a Job Card before the Job Card
    can be completed. QI.on_submit() calls update_qc_reference() which sets
    jc.quality_inspection automatically.
    """
    qi = frappe.get_doc({
        "doctype": "Quality Inspection",
        "reference_type": "Job Card",
        "reference_name": jc.name,
        "item_code": jc.production_item,
        "inspection_type": "In Process",
        "status": "Accepted",
        "manual_inspection": 1,
        "inspected_by": frappe.session.user,
        "sample_size": 1,
        "custom_inspection_form": inspection_form,
    })
    qi.insert()
    qi.submit()
    return qi.name


def create_and_submit_qi_for_se(se, row, inspection_form):
    """Create and submit a Quality Inspection for a specific Stock Entry row.

    Uses child_row_reference so QI binds back to the exact item row
    (ERPNext disambiguation when item_code repeats).
    """
    qi = frappe.get_doc({
        "doctype": "Quality Inspection",
        "reference_type": "Stock Entry",
        "reference_name": se.name,
        "child_row_reference": row.name,
        "item_code": row.item_code,
        "serial_no": row.serial_no,
        "batch_no": row.batch_no,
        "sample_size": row.sample_quantity or 1,
        "inspection_type": "Incoming",
        "status": "Accepted",
        "manual_inspection": 1,
        "inspected_by": frappe.session.user,
        "custom_inspection_form": inspection_form,
        "custom_skip_auto_submit": 1,
    })
    qi.insert()
    qi.submit()
    return qi.name
