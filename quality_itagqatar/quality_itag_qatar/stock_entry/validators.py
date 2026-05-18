"""Stock Entry validators — Quality concerns."""

import frappe
from frappe import _


def validate_inward_inspection_required(doc, method=None):
    """Block Stock Entry submit when inward inspection is required but no submitted QI exists."""
    if doc.docstatus != 1:
        return
    if not doc.get("custom_inward_inspection_required"):
        return
    if frappe.db.exists(
        "Quality Inspection",
        {
            "reference_type": "Stock Entry",
            "reference_name": doc.name,
            "docstatus": 1,
        },
    ):
        return
    frappe.throw(
        _(
            "A submitted Quality Inspection is required for this Stock Entry. "
            "Complete and submit the linked inspection report before submitting the Stock Entry."
        ),
        title=_("Quality Inspection Required"),
    )
