import frappe
from frappe import _

from quality_itagqatar.quality_itag_qatar.inspection import dispatcher


@frappe.whitelist()
def start_jc_inspection(job_card, inspection_form):
    if not job_card or not inspection_form:
        frappe.throw(_("Job Card and Inspection Form are required"))
    return dispatcher.start_inspection(job_card, inspection_form)
