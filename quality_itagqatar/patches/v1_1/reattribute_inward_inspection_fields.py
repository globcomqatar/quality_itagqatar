"""Re-attribute Custom Fields migrated from Globcom Manufacturing Custom to
Quality ITAG Qatar as part of the inward-inspection ownership cleanup.

Idempotent — safe to re-run. No-op for any field already attributed to the new module.
"""

import frappe

NEW_MODULE = "Quality ITAG Qatar"

FIELDS = [
    "Stock Entry-custom_inward_inspection_required",
    "Quality Inspection-custom_inward_serial_no",
]


def execute():
    changed = False
    for field_name in FIELDS:
        if not frappe.db.exists("Custom Field", field_name):
            continue
        current = frappe.db.get_value("Custom Field", field_name, "module")
        if current == NEW_MODULE:
            continue
        frappe.db.set_value("Custom Field", field_name, "module", NEW_MODULE)
        changed = True
    if changed:
        frappe.db.commit()
