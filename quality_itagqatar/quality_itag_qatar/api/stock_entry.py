import frappe
from frappe import _

from quality_itagqatar.quality_itag_qatar.inspection import dispatcher
from quality_itagqatar.quality_itag_qatar.inspection.constants import INSPECTION_FORMS


@frappe.whitelist()
def start_se_inspection(stock_entry, inspection_form, child_row_reference):
    if not stock_entry or not inspection_form or not child_row_reference:
        frappe.throw(_("Stock Entry, Inspection Form, and item row are required"))
    if inspection_form not in INSPECTION_FORMS:
        frappe.throw(_("Invalid inspection form: {0}").format(inspection_form))
    return dispatcher.start_inspection_from_se(stock_entry, inspection_form, child_row_reference)
