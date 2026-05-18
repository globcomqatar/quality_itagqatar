"""Additive dashboard override for Quality Inspection.

Appends a Quality Forms transactions group linking the 6 inspection report
doctypes. Reports link back via their `quality_inspection` Link field; that
fieldname is set as the dashboard default because Quality Inspection has no
upstream `*_dashboard.py`, so `data["fieldname"]` would otherwise be None
and Frappe's `get_external_links` would return zero counts.
"""

from frappe import _

QUALITY_REPORT_DOCTYPES = [
    "Assembly Traceability Record",
    "Certificate of Conformity",
    "Dimensional Inspection Report",
    "Final Machining Visual Examination Report",
    "QC Material Release Note",
    "Visual Examination Report",
]


def get_dashboard_data(data):
    data = data or {}
    data.setdefault("transactions", [])
    if not data.get("fieldname"):
        data["fieldname"] = "quality_inspection"

    data["transactions"].append({
        "label": _("Quality Forms"),
        "items": QUALITY_REPORT_DOCTYPES,
    })

    return data
