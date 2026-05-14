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
                    "Contract Review Record",
                    "Dimensional Inspection Report",
                    "Final Machining Visual Examination Report",
                    "QC Material Release Note",
                    "Visual Examination Report",
                ],
            ]
        ],
    },
]

doc_events = {
    "Quality Inspection": {
        "on_submit": "quality_itagqatar.quality_itag_qatar.quality_inspection.auto_submit.on_submit",
    },
    "Stock Entry": {
        "validate": "quality_itagqatar.quality_itag_qatar.stock_entry.validators.validate_inward_inspection_required",
    },
}

doctype_js = {
    "Job Card": "public/js/job_card.js",
    "Stock Entry": "public/js/stock_entry.js",
    "Quality Inspection": "public/js/quality_inspection.js",
    "Assembly Traceability Record": "public/js/inspection_report_common.js",
    "Certificate of Conformity": "public/js/inspection_report_common.js",
    "Contract Review Record": "public/js/inspection_report_common.js",
    "Dimensional Inspection Report": "public/js/inspection_report_common.js",
    "Final Machining Visual Examination Report": "public/js/inspection_report_common.js",
    "QC Material Release Note": "public/js/inspection_report_common.js",
    "Visual Examination Report": "public/js/inspection_report_common.js",
}
