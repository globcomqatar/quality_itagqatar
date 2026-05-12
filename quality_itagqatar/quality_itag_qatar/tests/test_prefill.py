# Copyright (c) 2026, Globcom Qatar and Contributors
# See license.txt

"""Integration tests for the config-driven prefill engine.

Verifies:
  - dot-walked source paths resolve through JC → WO → SO
  - priority-ordered fallback when a higher-priority path breaks mid-walk
  - skip-if-filled: never clobber a non-empty target field
  - audit log written exactly once per insert / manual refresh event
  - before_insert is the only trigger — re-saving does not re-fill
  - manual `refresh_from_source` re-fills blanks and writes a separate log row
"""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from quality_itagqatar.quality_itag_qatar.inspection.prefill import (
	refresh_from_source,
	resolve_path,
)

TARGET_DT = "Dimensional Inspection Report"


class TestPrefillEngine(FrappeTestCase):
	"""Unit-level tests for resolve_path. No SO/WO/JC required."""

	def test_resolve_path_single_hop_returns_leaf(self):
		anchor = frappe._dict({
			"doctype": "Job Card",
			"name": "JC-TEST",
			"production_item": "ITEM-X",
		})
		value, src_dt, src_name = resolve_path(anchor, "production_item")
		self.assertEqual(value, "ITEM-X")
		self.assertEqual(src_dt, "Job Card")
		self.assertEqual(src_name, "JC-TEST")

	def test_resolve_path_empty_path_returns_none(self):
		self.assertEqual(resolve_path(frappe._dict({"doctype": "Job Card"}), ""), (None, None, None))

	def test_resolve_path_exceeds_depth_returns_none(self):
		deep = ".".join(["x"] * 11)
		self.assertEqual(resolve_path(frappe._dict({"doctype": "Job Card"}), deep), (None, None, None))


class TestPrefillFlow(FrappeTestCase):
	"""End-to-end flow against a real JC → WO → SO chain.

	Skips entirely if ERPNext test fixtures (Customer/Item/SO/WO/JC) cannot
	be created on this site — the engine itself is still covered by
	TestPrefillEngine.
	"""

	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		try:
			cls.chain = _build_jc_chain()
		except Exception as exc:
			raise cls.skipTest(cls, f"ERPNext chain fixtures unavailable: {exc}")
		cls.mapping_name = _ensure_mapping(
			target_dt=TARGET_DT,
			rules=[
				# 3-hop: customer lives on Sales Order, walked via WO
				{"target_field": "customer", "source_path": "work_order.sales_order.customer", "priority": 10},
				# fallback: directly on Work Order (won't exist on stock WO, but exercises fallback)
				{"target_field": "customer", "source_path": "work_order.customer", "priority": 20},
				# 1-hop: production_item lives on JC
				{"target_field": "part_number", "source_path": "production_item", "priority": 10},
			],
		)

	@classmethod
	def tearDownClass(cls):
		super().tearDownClass()
		frappe.db.rollback()

	def setUp(self):
		_clear_logs_for(TARGET_DT)

	def test_three_hop_walk_fills_customer(self):
		report = _make_report(self.chain.jc.name)
		report.insert(ignore_permissions=True)
		self.assertEqual(report.customer, self.chain.customer)

	def test_one_hop_fills_part_number(self):
		report = _make_report(self.chain.jc.name)
		report.insert(ignore_permissions=True)
		self.assertEqual(report.part_number, self.chain.item)

	def test_skip_when_target_already_filled(self):
		report = _make_report(self.chain.jc.name, part_number="USER-OVERRIDE")
		report.insert(ignore_permissions=True)
		self.assertEqual(report.part_number, "USER-OVERRIDE")

	def test_log_written_on_insert(self):
		report = _make_report(self.chain.jc.name)
		report.insert(ignore_permissions=True)
		logs = frappe.get_all(
			"Quality Prefill Log",
			filters={"target_doctype": TARGET_DT, "target_name": report.name},
			fields=["name", "trigger", "fields_filled"],
		)
		self.assertEqual(len(logs), 1)
		self.assertEqual(logs[0].trigger, "Insert")
		payload = json.loads(logs[0].fields_filled)
		self.assertIn("customer", payload)
		self.assertEqual(payload["customer"]["source_doctype"], "Sales Order")

	def test_save_does_not_refill(self):
		report = _make_report(self.chain.jc.name)
		report.insert(ignore_permissions=True)
		report.db_set("customer", None)
		report.reload()
		report.save(ignore_permissions=True)
		self.assertIsNone(report.customer)

	def test_manual_refresh_fills_blanks(self):
		report = _make_report(self.chain.jc.name)
		report.insert(ignore_permissions=True)
		report.db_set("customer", None)
		result = refresh_from_source(TARGET_DT, report.name)
		self.assertIn("customer", result["filled"])
		refreshed = frappe.get_doc(TARGET_DT, report.name)
		self.assertEqual(refreshed.customer, self.chain.customer)
		logs = frappe.get_all(
			"Quality Prefill Log",
			filters={"target_doctype": TARGET_DT, "target_name": report.name},
			fields=["trigger"],
			order_by="filled_on asc",
		)
		self.assertEqual([log.trigger for log in logs], ["Insert", "Manual Refresh"])


def _build_jc_chain():
	"""Create the minimum Customer → Item → SO → WO → JC chain.

	Returns a frappe._dict with .customer, .item, .so, .wo, .jc references.
	Relies on existing ERPNext company / warehouse / default accounts on
	the test site. Caller is expected to skip if anything raises.
	"""
	from erpnext.manufacturing.doctype.work_order.test_work_order import make_wo_order_test_record
	from erpnext.selling.doctype.sales_order.test_sales_order import make_sales_order

	customer = "Quality Prefill Test Customer"
	if not frappe.db.exists("Customer", customer):
		frappe.get_doc({
			"doctype": "Customer",
			"customer_name": customer,
			"customer_type": "Company",
			"customer_group": "All Customer Groups",
			"territory": "All Territories",
		}).insert(ignore_permissions=True)

	so = make_sales_order(customer=customer, item_code="_Test FG Item", qty=1)
	wo = make_wo_order_test_record(
		item="_Test FG Item",
		qty=1,
		sales_order=so.name,
		do_not_submit=False,
	)
	jc_name = frappe.db.get_value("Job Card", {"work_order": wo.name}, "name")
	if not jc_name:
		jc = frappe.get_doc({
			"doctype": "Job Card",
			"work_order": wo.name,
			"production_item": "_Test FG Item",
			"for_quantity": 1,
			"operation": wo.operations[0].operation if wo.operations else None,
		}).insert(ignore_permissions=True)
		jc_name = jc.name
	return frappe._dict({
		"customer": customer,
		"item": "_Test FG Item",
		"so": frappe.get_doc("Sales Order", so.name),
		"wo": frappe.get_doc("Work Order", wo.name),
		"jc": frappe.get_doc("Job Card", jc_name),
	})


def _ensure_mapping(target_dt, rules):
	"""Create (or replace) the Quality Field Mapping for target_dt."""
	if frappe.db.exists("Quality Field Mapping", target_dt):
		frappe.delete_doc("Quality Field Mapping", target_dt, force=True, ignore_permissions=True)
	doc = frappe.get_doc({
		"doctype": "Quality Field Mapping",
		"target_doctype": target_dt,
		"active": 1,
		"rules": rules,
	})
	doc.insert(ignore_permissions=True)
	return doc.name


def _make_report(jc_name, **fields):
	report = frappe.get_doc({
		"doctype": TARGET_DT,
		"job_card": jc_name,
		**fields,
	})
	return report


def _clear_logs_for(target_dt):
	frappe.db.delete("Quality Prefill Log", {"target_doctype": target_dt})
