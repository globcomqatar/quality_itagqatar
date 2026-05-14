# Copyright (c) 2026, Globcom Qatar and contributors
# For license information, please see license.txt

"""
Config-driven prefill engine for Quality Report DocTypes.

Mapping rules live in `Quality Field Mapping` (one record per target DocType).
Each rule declares a source DocType and a dot-walked path from that anchor to
the source value. Multiple rules per target field are tried in priority order;
first non-empty wins. Targets that are already filled are never overwritten.

Engine entry points:
- prefill_target(target_doc, trigger)  → invoked from PrefillMixin.before_insert
- refresh_from_source(doctype, name)   → whitelisted, called by client button
"""

import frappe
from frappe import _

MAX_PATH_DEPTH = 10
TRIGGER_INSERT = "Insert"
TRIGGER_MANUAL = "Manual Refresh"
DEFAULT_SOURCE_DOCTYPE = "Job Card"


def prefill_target(target_doc, trigger=TRIGGER_INSERT):
	"""Apply mapping rules to target_doc in-place.

	Returns dict {target_field: {source_doctype, source_name, value}} for
	fields that were actually filled. Empty dict if nothing matched or any
	precondition failed. Never raises — failures are logged.
	"""
	try:
		mapping = _load_mapping(target_doc.doctype)
		if not mapping or not mapping.active:
			return {}
		target_meta = frappe.get_meta(target_doc.doctype)
		anchors_cache: dict[str, object | None] = {}
		filled = {}
		for tgt_field, rules in _group_active_rules_by_target(mapping.rules).items():
			tgt_field_meta = target_meta.get_field(tgt_field)
			if not tgt_field_meta:
				continue
			if _is_filled(target_doc.get(tgt_field)):
				continue
			for rule in sorted(rules, key=lambda r: r.priority):
				source_doctype = rule.source_doctype or DEFAULT_SOURCE_DOCTYPE
				if source_doctype not in anchors_cache:
					anchors_cache[source_doctype] = _load_anchor(target_doc, source_doctype)
				anchor = anchors_cache[source_doctype]
				if not anchor:
					continue
				value, src_dt, src_name = resolve_path(anchor, rule.source_path)
				if not _is_filled(value):
					continue
				if not _typecheck_ok(tgt_field_meta, value):
					continue
				target_doc.set(tgt_field, value)
				filled[tgt_field] = {
					"source_doctype": src_dt,
					"source_name": src_name,
					"value": value,
				}
				break
		return filled
	except Exception:
		frappe.log_error(
			title="Quality Prefill Failed",
			message=frappe.get_traceback(),
		)
		return {}


def resolve_path(anchor_doc, path):
	"""Dot-walk Link fields from anchor.

	Returns (value, source_doctype, source_name). Broken or non-Link hops
	return (None, None, None) — the caller treats this as "rule does not match".
	"""
	if not path:
		return (None, None, None)
	parts = path.split(".")
	if len(parts) > MAX_PATH_DEPTH:
		return (None, None, None)
	current = anchor_doc
	for hop in parts[:-1]:
		link_value = current.get(hop)
		if not link_value:
			return (None, None, None)
		link_field = frappe.get_meta(current.doctype).get_field(hop)
		if not link_field or link_field.fieldtype != "Link":
			return (None, None, None)
		try:
			current = frappe.get_cached_doc(link_field.options, link_value)
		except frappe.DoesNotExistError:
			return (None, None, None)
	leaf_field = frappe.get_meta(current.doctype).get_field(parts[-1])
	if leaf_field and leaf_field.fieldtype == "Table":
		return (None, None, None)
	return (current.get(parts[-1]), current.doctype, current.name)


@frappe.whitelist()
def refresh_from_source(doctype, name):
	"""Manual re-run from the report form's 'Refresh from Source' button."""
	if not frappe.has_permission(doctype, "write", doc=name):
		frappe.throw(_("No write permission on {0}").format(doctype), frappe.PermissionError)
	doc = frappe.get_doc(doctype, name)
	filled = prefill_target(doc, trigger=TRIGGER_MANUAL)
	if filled:
		doc.save()
		_write_log(doc, filled, TRIGGER_MANUAL)
	return {"filled": filled}


def _load_anchor(target_doc, source_doctype):
	"""Resolve the target's Link → source_doctype field and load that anchor.

	Asserts exactly one such field. Returns None if zero, more than one,
	or the field is empty / anchor row missing.
	"""
	meta = frappe.get_meta(target_doc.doctype)
	candidates = [
		f.fieldname for f in meta.fields if f.fieldtype == "Link" and f.options == source_doctype
	]
	if len(candidates) != 1:
		if len(candidates) > 1:
			frappe.log_error(
				title="Quality Prefill: ambiguous anchor",
				message=f"{target_doc.doctype} has {len(candidates)} Link→{source_doctype} fields: {candidates}",
			)
		return None
	anchor_name = target_doc.get(candidates[0])
	if not anchor_name:
		return None
	try:
		return frappe.get_cached_doc(source_doctype, anchor_name)
	except frappe.DoesNotExistError:
		return None


def _load_mapping(target_doctype):
	"""Load the Quality Field Mapping record for target_doctype, or None.

	target_doctype is unique on the mapping, so a single get_value lookup
	resolves to the record name (now from the naming series, not the
	target_doctype string).
	"""
	name = frappe.db.get_value("Quality Field Mapping", {"target_doctype": target_doctype}, "name")
	if not name:
		return None
	return frappe.get_cached_doc("Quality Field Mapping", name)


def _group_active_rules_by_target(rules):
	grouped = {}
	for rule in rules:
		if not rule.active:
			continue
		if not rule.target_field or not rule.source_path:
			continue
		grouped.setdefault(rule.target_field, []).append(rule)
	return grouped


def _is_filled(value):
	if value is None:
		return False
	if isinstance(value, str) and not value.strip():
		return False
	return True


def _typecheck_ok(target_field_meta, value):
	"""Reject obvious type mismatches before assigning.

	Link targets must resolve to an existing record of the linked DocType.
	Other fieldtypes pass through — Frappe will coerce on save.
	"""
	if target_field_meta.fieldtype == "Link" and target_field_meta.options:
		return bool(frappe.db.exists(target_field_meta.options, value))
	return True


def _write_log(target_doc, filled, trigger):
	"""Insert one Quality Prefill Log row per prefill event."""
	frappe.get_doc({
		"doctype": "Quality Prefill Log",
		"target_doctype": target_doc.doctype,
		"target_name": target_doc.name,
		"trigger": trigger,
		"fields_filled": frappe.as_json(filled),
		"source_summary": _summarize_sources(filled),
	}).insert(ignore_permissions=True)


def _summarize_sources(filled):
	seen = []
	for entry in filled.values():
		token = f"{entry['source_doctype']}:{entry['source_name']}"
		if token not in seen:
			seen.append(token)
	return ", ".join(seen)
