app_name = "quality_itagqatar"
app_title = "Quality ITAG Qatar"
app_publisher = "Globcom Qatar"
app_description = "Quality Module Custom Development for ITAG Qatar"
app_email = "info@globcomqatar.com"
app_license = "mit"

required_apps = ["erpnext"]

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [["module", "=", "Quality ITAG Qatar"]],
    },
    {
        "dt": "Property Setter",
        "filters": [["module", "=", "Quality ITAG Qatar"]],
    },
    {
        "dt": "Quality Field Mapping",
        "filters": [
            [
                "target_doctype",
                "in",
                [
                    "Assembly Traceability Record",
                    "Certificate of Conformity",
                    "Dimensional Inspection Report",
                    "Final Machining Visual Examination Report",
                    "QC Material Release Note",
                    "Visual Examination Report",
                ],
            ]
        ],
    },
]

_INSPECTION_REPORT_DOCTYPES = [
    "Assembly Traceability Record",
    "Certificate of Conformity",
    "Dimensional Inspection Report",
    "Final Machining Visual Examination Report",
    "QC Material Release Note",
    "Visual Examination Report",
]

doc_events = {
    "Stock Entry": {
        "validate": "quality_itagqatar.quality_itag_qatar.stock_entry.validators.validate_inward_inspection_required",
    },
    **{
        dt: {
            "on_submit": "quality_itagqatar.quality_itag_qatar.inspection.qi_bridge.submit_linked_qi",
        }
        for dt in _INSPECTION_REPORT_DOCTYPES
    },
}

doctype_js = {
    "Job Card": "public/js/job_card.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Quality Inspection": "public/js/quality_inspection.js",
    **{dt: "public/js/inspection_report_common.js" for dt in _INSPECTION_REPORT_DOCTYPES},
}

override_doctype_dashboards = {
    "Stock Entry": "quality_itagqatar.quality_itag_qatar.stock_entry.dashboard.get_dashboard_data",
    "Quality Inspection": "quality_itagqatar.quality_itag_qatar.quality_inspection.dashboard.get_dashboard_data",
}
