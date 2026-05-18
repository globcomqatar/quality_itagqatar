"""Additive dashboard override for Stock Entry.

Receives the standard dashboard payload and appends a Quality group linking
the 6 inspection report doctypes (native stock_entry field, default snake_case
matches Frappe's auto-mapping) and Quality Inspection (which uses a dynamic
reference_type/reference_name pair, mapped via non_standard_fieldnames).
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
    data.setdefault("non_standard_fieldnames", {})

    data["transactions"].append({
        "label": _("Quality"),
        "items": ["Quality Inspection", *QUALITY_REPORT_DOCTYPES],
    })

    data["non_standard_fieldnames"]["Quality Inspection"] = "reference_name"

    return data
