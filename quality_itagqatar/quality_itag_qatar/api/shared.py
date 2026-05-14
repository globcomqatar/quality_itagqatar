import frappe

from quality_itagqatar.quality_itag_qatar.inspection.constants import INSPECTION_FORMS


@frappe.whitelist()
def get_inspection_forms() -> list[str]:
	return list(INSPECTION_FORMS)
