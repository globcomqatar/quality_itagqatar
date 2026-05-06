"""Re-attribute quality DocTypes and Custom Fields from ERPCloud ITAG Qatar
to Quality ITAG Qatar after the code split.

Idempotent — safe to re-run.
"""

import frappe

OLD_MODULE = "ERPCloud ITAG Qatar"
NEW_MODULE = "Quality ITAG Qatar"

QUALITY_DOCTYPES = [
    "Assembly Traceability Record",
    "Assembly Traceability Record Details",
    "Certificate of Conformity",
    "Certificate of Conformity Details",
    "Contract Review Record",
    "Contract Review Record Details",
    "Dimensional Inspection Report",
    "Dimensional Inspection Details",
    "Final Machining Visual Examination Report",
    "Final Machining Visual Examination Report Details",
    "QC Material Release Note",
    "QC Material Release Note Details",
    "Visual Examination Report",
    "Visual Examination Details",
    "Inspection Evidence Attachment",
]

QUALITY_CUSTOM_FIELDS = [
    "Quality Inspection-custom_inspection_form",
    "Quality Inspection-custom_start_inspection",
    "Job Card-custom_quality_forms",
    "Job Card-custom_inspection_form",
    "Job Card-custom_start_inspection",
]


def execute():
    _ensure_module_def_exists()
    _reattribute_doctypes()
    _reattribute_custom_fields()
    _reattribute_workspaces()
    frappe.db.commit()


def _ensure_module_def_exists():
    if frappe.db.exists("Module Def", NEW_MODULE):
        return
    frappe.get_doc({
        "doctype": "Module Def",
        "module_name": NEW_MODULE,
        "app_name": "quality_itagqatar",
    }).insert(ignore_permissions=True)


def _reattribute_doctypes():
    for dt in QUALITY_DOCTYPES:
        if not frappe.db.exists("DocType", dt):
            continue
        current = frappe.db.get_value("DocType", dt, "module")
        if current == NEW_MODULE:
            continue
        frappe.db.set_value("DocType", dt, "module", NEW_MODULE)


def _reattribute_custom_fields():
    for cf in QUALITY_CUSTOM_FIELDS:
        if not frappe.db.exists("Custom Field", cf):
            continue
        current = frappe.db.get_value("Custom Field", cf, "module")
        if current == NEW_MODULE:
            continue
        frappe.db.set_value("Custom Field", cf, "module", NEW_MODULE)


def _reattribute_workspaces():
    """Flip any Workspace whose module is the old one AND whose name matches a
    quality DocType. Defensive — no-op when no such Workspace exists.
    """
    candidates = frappe.get_all(
        "Workspace",
        filters={"module": OLD_MODULE, "name": ["in", QUALITY_DOCTYPES]},
        pluck="name",
    )
    for ws in candidates:
        frappe.db.set_value("Workspace", ws, "module", NEW_MODULE)
