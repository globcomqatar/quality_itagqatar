"""
Job Card → Quality Reports prefill engine.

Public entry: `prefill_from_job_card(target_doc)` — call from each parent
report controller's `validate()`. Fills empty fields from the JC chain
(JC → WO → SO). Skips already-filled fields so user edits survive.
Never raises — failures go to the error log.
"""

import frappe

from quality_itagqatar.quality_itag_qatar.inspection.mapping_config import (
	BLOCK_FIELDS,
	SAFE_FIELDTYPES,
	SOURCE_CHAIN,
)


def _job_card_fieldname(target_doc):
	"""Resolve the Link → Job Card field on target_doc (matches report_factory)."""
	meta = frappe.get_meta(target_doc.doctype)
	return next(
		(f.fieldname for f in meta.fields if f.fieldtype == "Link" and f.options == "Job Card"),
		None,
	)


def _is_filled(value):
	return value not in (None, "", 0, 0.0, [])


def build_source_chain(target_doc):
	"""Return [JC, WO, SO] in priority order. Missing links → shorter list, no raise."""
	jc_field = _job_card_fieldname(target_doc)
	if not jc_field:
		return []

	jc_name = target_doc.get(jc_field)
	if not jc_name:
		return []

	chain = [frappe.get_cached_doc("Job Card", jc_name)]
	cursor = chain[0]

	for parent_attr, next_dt in SOURCE_CHAIN:
		next_name = cursor.get(parent_attr)
		if not next_name:
			break
		next_doc = frappe.get_cached_doc(next_dt, next_name)
		chain.append(next_doc)
		cursor = next_doc

	return chain


def prefill_from_job_card(target_doc):
	"""Fill empty target fields from JC chain. Skip already-filled. Never raise."""
	try:
		chain = build_source_chain(target_doc)
		if not chain:
			return

		target_meta = frappe.get_meta(target_doc.doctype)
		overrides = getattr(type(target_doc), "MAPPING_OVERRIDES", {}) or {}
		jc_field = _job_card_fieldname(target_doc)
		blocked = BLOCK_FIELDS | ({jc_field} if jc_field else set())

		_auto_match(target_doc, target_meta, chain, blocked)
		_apply_overrides(target_doc, target_meta, chain, overrides, blocked)

	except Exception:
		frappe.log_error(
			title="quality_itagqatar prefill_from_job_card failed",
			message=frappe.get_traceback(),
		)


def _auto_match(target_doc, target_meta, chain, blocked):
	for tgt_field in target_meta.fields:
		if tgt_field.fieldname in blocked:
			continue
		if tgt_field.fieldtype not in SAFE_FIELDTYPES:
			continue
		if _is_filled(target_doc.get(tgt_field.fieldname)):
			continue

		for source_doc in chain:
			src_meta = frappe.get_meta(source_doc.doctype)
			src_field = src_meta.get_field(tgt_field.fieldname)
			if not src_field or src_field.fieldtype not in SAFE_FIELDTYPES:
				continue
			src_value = source_doc.get(tgt_field.fieldname)
			if not _is_filled(src_value):
				continue
			target_doc.set(tgt_field.fieldname, src_value)
			break


def _apply_overrides(target_doc, target_meta, chain, overrides, blocked):
	for source_doc in chain:
		src_overrides = overrides.get(source_doc.doctype) or {}
		for src_fieldname, tgt_fieldname in src_overrides.items():
			if tgt_fieldname in blocked:
				continue
			tgt_meta_field = target_meta.get_field(tgt_fieldname)
			if not tgt_meta_field or tgt_meta_field.fieldtype not in SAFE_FIELDTYPES:
				continue
			if _is_filled(target_doc.get(tgt_fieldname)):
				continue
			src_value = source_doc.get(src_fieldname)
			if not _is_filled(src_value):
				continue
			target_doc.set(tgt_fieldname, src_value)
