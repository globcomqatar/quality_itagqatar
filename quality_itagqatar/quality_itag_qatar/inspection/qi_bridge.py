import frappe
from frappe import _


def create_and_submit_qi(jc, inspection_form):
    """Create and submit a Quality Inspection silently.

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
