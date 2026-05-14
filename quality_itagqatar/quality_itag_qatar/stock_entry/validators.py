"""Stock Entry validators — Quality concerns.

Migrated from globcom_manufacturing on 2026-05-14 as part of consolidating
ownership of inward inspection under quality_itagqatar.
"""

import frappe
from frappe import _


def validate_inward_inspection_required(doc, method=None):
    """Block Stock Entry submit when inward inspection is required but no QI exists."""
    if doc.docstatus != 1:
        return
    if not doc.get("custom_inward_inspection_required"):
        return
    if frappe.db.exists(
        "Quality Inspection",
        {"reference_type": "Stock Entry", "reference_name": doc.name},
    ):
        return
    frappe.throw(
        _("Quality Inspection is required for this Stock Entry. Please create Quality Inspection before submitting."),
        title=_("Quality Inspection Required"),
    )
