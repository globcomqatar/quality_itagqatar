import frappe
from frappe import _

from quality_itagqatar.quality_itag_qatar.inspection.hooks import run_hook


def create_report(inspection_form, qi_name):
    if not frappe.db.exists("DocType", inspection_form):
        frappe.throw(_("Invalid inspection form: {0}").format(inspection_form))
    if not frappe.has_permission(inspection_form, "create"):
        frappe.throw(_("No permission to create {0}").format(inspection_form))

    report = frappe.get_doc({
        "doctype": inspection_form,
        "quality_inspection": qi_name,
    })

    _apply_common_fields(report, qi_name)
    run_hook(inspection_form, "before_create", qi_name, report)
    report.insert()
    run_hook(inspection_form, "after_create", qi_name, report)

    return {"doctype": inspection_form, "name": report.name}


def _apply_common_fields(report, qi_name):
    qi = frappe.get_cached_doc("Quality Inspection", qi_name)
    if not qi.reference_type or not qi.reference_name:
        return
    meta = frappe.get_meta(report.doctype)
    anchor_field = next(
        (f.fieldname for f in meta.fields if f.fieldtype == "Link" and f.options == qi.reference_type),
        None,
    )
    if anchor_field:
        report.set(anchor_field, qi.reference_name)
