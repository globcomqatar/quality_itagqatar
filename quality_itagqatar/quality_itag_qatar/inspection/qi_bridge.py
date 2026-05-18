import frappe
from frappe import _


def create_qi_for_jc(jc, inspection_form):
    """Create a Draft Quality Inspection for a Job Card.

    QI stays in Draft. It is only submitted when the linked inspection report
    (e.g. Dimensional Inspection Report) is submitted — see submit_linked_qi.
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
    })
    qi.insert()
    return qi.name


def create_qi_for_se(se, row, inspection_form):
    """Create a Draft Quality Inspection for a specific Stock Entry row.

    Uses child_row_reference to disambiguate when item_code repeats. QI stays
    in Draft; submission is deferred to inspection-report submit.
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
    })
    qi.insert()
    return qi.name


def submit_linked_qi(report_doc, method=None):
    """Submit the Quality Inspection linked to an inspection report on report submit.

    Wired via doc_events.on_submit for the 6 inspection report doctypes in hooks.py.
    """
    qi_name = report_doc.get("quality_inspection")
    if not qi_name:
        return
    qi = frappe.get_doc("Quality Inspection", qi_name)
    if qi.docstatus != 0:
        return
    qi.submit()
