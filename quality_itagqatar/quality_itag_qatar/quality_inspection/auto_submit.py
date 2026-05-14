"""Quality Inspection on_submit handler — Stock Entry auto-submit cascade.

Migrated from globcom_manufacturing on 2026-05-14. The previous owner blocked QI
submission whenever the linked SE failed to submit, which caused real-world 417s
when the SE wasn't yet ready (e.g. our Start Inspection flow on a draft SE).

`custom_skip_auto_submit` short-circuits the cascade — set by
`inspection.qi_bridge.create_and_submit_qi_for_se` so our flow never auto-submits
a still-draft SE.
"""

import frappe
from frappe import _


def on_submit(doc, method=None):
    if doc.get("custom_skip_auto_submit"):
        return
    if doc.reference_type == "Stock Entry" and doc.reference_name:
        auto_submit_stock_entry(doc)


def auto_submit_stock_entry(doc):
    try:
        stock_entry = frappe.get_doc("Stock Entry", doc.reference_name)
    except frappe.DoesNotExistError:
        frappe.throw(
            _("Stock Entry {0} does not exist").format(doc.reference_name),
            title=_("Stock Entry Not Found"),
        )
        return

    if stock_entry.docstatus == 0:
        try:
            stock_entry.submit()
            frappe.msgprint(
                _("Stock Entry {0} has been submitted automatically").format(doc.reference_name),
                indicator="green",
                alert=True,
            )
        except frappe.ValidationError as e:
            frappe.throw(
                _("Cannot submit Quality Inspection because Stock Entry {0} has validation errors: {1}").format(
                    doc.reference_name, str(e)
                ),
                title=_("Stock Entry Validation Failed"),
            )
        except Exception as e:
            frappe.throw(
                _("Cannot submit Quality Inspection because Stock Entry {0} submission failed: {1}").format(
                    doc.reference_name, str(e)
                ),
                title=_("Stock Entry Submission Failed"),
            )
    elif stock_entry.docstatus == 2:
        frappe.msgprint(
            _("Stock Entry {0} is cancelled. Cannot auto-submit.").format(doc.reference_name),
            indicator="orange",
            alert=True,
        )
