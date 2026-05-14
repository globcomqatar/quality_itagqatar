import frappe
from frappe import _

from quality_itagqatar.quality_itag_qatar.inspection import qi_bridge, report_factory


def start_inspection(job_card, inspection_form):
    jc = frappe.get_doc("Job Card", job_card)
    if not jc.has_permission("write"):
        frappe.throw(_("Insufficient permissions on Job Card"))

    qi_name = qi_bridge.create_and_submit_qi(jc, inspection_form)
    return report_factory.create_report(inspection_form, qi_name)


def start_inspection_from_se(stock_entry, inspection_form, child_row_reference):
    se = frappe.get_doc("Stock Entry", stock_entry)
    if not se.has_permission("write"):
        frappe.throw(_("Insufficient permissions on Stock Entry"))

    row = next((d for d in se.items if d.name == child_row_reference), None)
    if not row:
        frappe.throw(_("Item row {0} not found on this Stock Entry").format(child_row_reference))

    qi_name = qi_bridge.create_and_submit_qi_for_se(se, row, inspection_form)
    return report_factory.create_report(inspection_form, qi_name)
