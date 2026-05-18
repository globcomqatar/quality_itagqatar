"""Cleanup patch — QI leftover fields + Contract Review Record + rename custom_stock_entry → stock_entry.

Idempotent. Runs once per site.

Quality Inspection: drops the legacy Start Inspection trio
    (custom_inspection_form, custom_start_inspection, custom_skip_auto_submit)
    — Custom Field rows, columns, property setters.

Contract Review Record: removes the doctype, its child table, all custom fields
    targeting it, property setters, and Quality Field Mapping rows pointing at it.

Owned report doctypes (Assembly Traceability Record, QC Material Release Note,
Certificate of Conformity, Visual Examination Report, Final Machining Visual
Examination Report, Dimensional Inspection Report): migrate the legacy Custom
Field `custom_stock_entry` to the native field `stock_entry` declared in each
doctype JSON. Copies non-null values from the old column to the new column,
drops the old column, and clears the orphan Custom Field rows.
"""

import frappe

QI_LEFTOVER_FIELDS = (
    "custom_inspection_form",
    "custom_start_inspection",
    "custom_skip_auto_submit",
    "custom_quality_forms_tab",
    "custom_quality_forms_html",
)

CRR_PARENT = "Contract Review Record"
CRR_CHILD = "Contract Review Record Details"

OWNED_REPORT_DOCTYPES = (
    "Assembly Traceability Record",
    "QC Material Release Note",
    "Certificate of Conformity",
    "Visual Examination Report",
    "Final Machining Visual Examination Report",
    "Dimensional Inspection Report",
)


def execute():
    _drop_qi_leftover_fields()
    _drop_contract_review_record()
    _migrate_custom_stock_entry()
    frappe.db.commit()


def _migrate_custom_stock_entry():
    for doctype in OWNED_REPORT_DOCTYPES:
        table = f"tab{doctype}"
        columns = _table_columns(table)
        if "custom_stock_entry" in columns:
            if "stock_entry" in columns:
                frappe.db.sql(
                    f"UPDATE `{table}` SET stock_entry = custom_stock_entry "
                    "WHERE custom_stock_entry IS NOT NULL "
                    "AND (stock_entry IS NULL OR stock_entry = '')"
                )
            try:
                frappe.db.sql_ddl(
                    f"ALTER TABLE `{table}` DROP COLUMN `custom_stock_entry`"
                )
            except Exception as e:  # noqa: BLE001
                frappe.log_error(
                    title=f"v1_2 drop {doctype}.custom_stock_entry",
                    message=f"Skipped: {e}",
                )

        frappe.db.sql(
            "DELETE FROM `tabCustom Field` WHERE dt=%s AND fieldname=%s",
            (doctype, "custom_stock_entry"),
        )
        frappe.db.sql(
            "DELETE FROM `tabProperty Setter` WHERE doc_type=%s AND field_name=%s",
            (doctype, "custom_stock_entry"),
        )


def _drop_qi_leftover_fields():
    qi_columns = _table_columns("tabQuality Inspection")
    for fieldname in QI_LEFTOVER_FIELDS:
        frappe.db.sql(
            "DELETE FROM `tabCustom Field` WHERE dt=%s AND fieldname=%s",
            ("Quality Inspection", fieldname),
        )
        frappe.db.sql(
            "DELETE FROM `tabProperty Setter` WHERE doc_type=%s AND field_name=%s",
            ("Quality Inspection", fieldname),
        )
        if fieldname in qi_columns:
            try:
                frappe.db.sql_ddl(
                    f"ALTER TABLE `tabQuality Inspection` DROP COLUMN `{fieldname}`"
                )
            except Exception as e:  # noqa: BLE001
                frappe.log_error(
                    title=f"v1_2 drop column {fieldname}",
                    message=f"Skipped: {e}",
                )


def _drop_contract_review_record():
    for dt in (CRR_PARENT, CRR_CHILD):
        frappe.db.sql(f"DROP TABLE IF EXISTS `tab{dt}`")

    if frappe.db.exists("Quality Field Mapping", {"target_doctype": CRR_PARENT}):
        mapping_names = frappe.get_all(
            "Quality Field Mapping",
            filters={"target_doctype": CRR_PARENT},
            pluck="name",
        )
        for name in mapping_names:
            frappe.db.sql(
                "DELETE FROM `tabQuality Field Mapping Rule` WHERE parent=%s",
                (name,),
            )
            frappe.db.sql(
                "DELETE FROM `tabQuality Field Mapping` WHERE name=%s",
                (name,),
            )

    frappe.db.sql(
        "DELETE FROM `tabCustom Field` WHERE dt IN (%s, %s)",
        (CRR_PARENT, CRR_CHILD),
    )
    frappe.db.sql(
        "DELETE FROM `tabProperty Setter` WHERE doc_type IN (%s, %s)",
        (CRR_PARENT, CRR_CHILD),
    )

    for dt in (CRR_PARENT, CRR_CHILD):
        if frappe.db.exists("DocType", dt):
            try:
                frappe.delete_doc(
                    "DocType", dt, force=1, ignore_permissions=True, ignore_missing=True
                )
            except Exception as e:  # noqa: BLE001
                frappe.log_error(
                    title=f"v1_2 delete DocType {dt}",
                    message=f"Skipped: {e}",
                )


def _table_columns(table_name):
    try:
        rows = frappe.db.sql(
            f"SHOW COLUMNS FROM `{table_name}`",
            as_dict=True,
        )
        return {r["Field"] for r in rows}
    except Exception:  # noqa: BLE001
        return set()
