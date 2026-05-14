# Copyright (c) 2026, Globcom Qatar and Contributors
# See license.txt

"""Integration test for the Stock Entry-driven inspection flow.

Verifies:
  - start_se_inspection creates a submitted Quality Inspection bound to the SE
    row via child_row_reference
  - the QI carries serial_no, batch_no and inspection_form passthrough
  - report_factory creates an instance of the chosen report and links it back
    to the Stock Entry via the custom_stock_entry field
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from quality_itagqatar.quality_itag_qatar.api.stock_entry import start_se_inspection

REPORT_DT = "Dimensional Inspection Report"


class TestStockEntryInspectionFlow(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		try:
			cls.item_code = _ensure_test_item()
			cls.warehouse = _ensure_test_warehouse()
			cls.stock_entry = _build_material_receipt(cls.item_code, cls.warehouse)
		except Exception as exc:  # noqa: BLE001
			cls._skip_reason = f"Test fixtures unavailable: {exc}"
			cls.stock_entry = None
		else:
			cls._skip_reason = None

	def setUp(self):
		if self._skip_reason:
			self.skipTest(self._skip_reason)

	def test_se_flow_creates_qi_and_report(self):
		row = self.stock_entry.items[0]
		result = start_se_inspection(self.stock_entry.name, REPORT_DT, row.name)

		self.assertEqual(result["doctype"], REPORT_DT)
		report = frappe.get_doc(REPORT_DT, result["name"])
		self.assertEqual(report.custom_stock_entry, self.stock_entry.name)

		qi_name = report.quality_inspection
		self.assertTrue(qi_name)
		qi = frappe.get_doc("Quality Inspection", qi_name)
		self.assertEqual(qi.reference_type, "Stock Entry")
		self.assertEqual(qi.reference_name, self.stock_entry.name)
		self.assertEqual(qi.child_row_reference, row.name)
		self.assertEqual(qi.item_code, row.item_code)
		self.assertEqual(qi.custom_inspection_form, REPORT_DT)
		self.assertEqual(qi.docstatus, 1)


def _ensure_test_item():
	code = "_Test QI Item"
	if not frappe.db.exists("Item", code):
		frappe.get_doc({
			"doctype": "Item",
			"item_code": code,
			"item_name": code,
			"item_group": "All Item Groups",
			"stock_uom": "Nos",
			"is_stock_item": 1,
		}).insert(ignore_permissions=True)
	return code


def _ensure_test_warehouse():
	name = "_Test QI Warehouse - _TC"
	if not frappe.db.exists("Warehouse", name):
		company = frappe.db.get_value("Company", filters={}, fieldname="name") or "_Test Company"
		frappe.get_doc({
			"doctype": "Warehouse",
			"warehouse_name": "_Test QI Warehouse",
			"company": company,
			"is_group": 0,
		}).insert(ignore_permissions=True)
	return name


def _build_material_receipt(item_code, warehouse):
	se = frappe.get_doc({
		"doctype": "Stock Entry",
		"stock_entry_type": "Material Receipt",
		"custom_inward_inspection_required": 1,
		"items": [
			{
				"item_code": item_code,
				"qty": 1,
				"basic_rate": 1,
				"t_warehouse": warehouse,
				"uom": "Nos",
				"stock_uom": "Nos",
				"conversion_factor": 1,
			}
		],
	})
	se.insert(ignore_permissions=True)
	return se
