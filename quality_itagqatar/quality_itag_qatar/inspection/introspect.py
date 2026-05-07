"""
One-shot field discovery for the JC → Quality Reports prefill mapper.

Run via bench console:
    bench --site SITE console
    >>> from quality_itagqatar.quality_itag_qatar.inspection.introspect import dump
    >>> dump()                          # markdown to stdout
    >>> dump(write_to_file=True)        # also writes .fb/features/f005-.../introspect-output.md

Not wired into runtime. Safe to run repeatedly.
"""

import os

import frappe

from quality_itagqatar.quality_itag_qatar.inspection.mapping_config import (
	BLOCK_FIELDS,
	SAFE_FIELDTYPES,
)

PARENT_REPORTS = (
	"Assembly Traceability Record",
	"Certificate of Conformity",
	"Contract Review Record",
	"Dimensional Inspection Report",
	"Final Machining Visual Examination Report",
	"QC Material Release Note",
	"Visual Examination Report",
)

SOURCE_DOCTYPES = ("Job Card", "Work Order", "Sales Order")


def _eligible_fields(doctype):
	"""{fieldname: fieldtype} — safe type, not blocked. Same filter the mapper uses on targets."""
	meta = frappe.get_meta(doctype)
	return {
		f.fieldname: f.fieldtype
		for f in meta.fields
		if f.fieldname not in BLOCK_FIELDS and f.fieldtype in SAFE_FIELDTYPES
	}


def _named_fields(doctype):
	"""{fieldname: fieldtype} — all fields minus block list, used for source side."""
	meta = frappe.get_meta(doctype)
	return {f.fieldname: f.fieldtype for f in meta.fields if f.fieldname not in BLOCK_FIELDS}


def _report_section(report_dt, source_field_maps):
	target = _eligible_fields(report_dt)
	if not target:
		return f"## {report_dt}\n\n_(no eligible target fields)_\n"

	lines = [f"## {report_dt}", "", f"Eligible target fields: **{len(target)}**", ""]

	matches_by_source = {}
	for src_dt, src_fields in source_field_maps.items():
		matches_by_source[src_dt] = sorted(
			(name, target[name], src_fields[name])
			for name in target
			if name in src_fields
		)

	lines += ["### Same-name matches (auto-prefilled)", ""]
	any_match = False
	for src_dt in SOURCE_DOCTYPES:
		hits = matches_by_source.get(src_dt) or []
		if not hits:
			continue
		any_match = True
		lines.append(f"**{src_dt}** — {len(hits)} field(s):")
		for name, tgt_type, src_type in hits:
			drift = "" if tgt_type == src_type else f"  _(type drift: src={src_type}, tgt={tgt_type})_"
			lines.append(f"- `{name}` ({tgt_type}){drift}")
		lines.append("")
	if not any_match:
		lines += ["_(none)_", ""]

	lines += ["### Unmatched target fields (candidates for MAPPING_OVERRIDES)", ""]
	matched = {n for hits in matches_by_source.values() for n, _, _ in hits}
	unmatched = sorted(set(target) - matched)
	if not unmatched:
		lines.append("_(none — full coverage)_")
	else:
		for name in unmatched:
			lines.append(f"- `{name}` ({target[name]})")
	lines.append("")
	return "\n".join(lines)


def dump(write_to_file=False):
	source_field_maps = {dt: _named_fields(dt) for dt in SOURCE_DOCTYPES}

	parts = [
		"# Field Discovery — Job Card → Quality Reports",
		"",
		f"Source chain (priority): {' → '.join(SOURCE_DOCTYPES)}",
		"",
		f"Safe fieldtypes: {sorted(SAFE_FIELDTYPES)}",
		"",
	]
	for report in PARENT_REPORTS:
		parts.append(_report_section(report, source_field_maps))

	output = "\n".join(parts)
	print(output)

	if write_to_file:
		app_root = os.path.dirname(frappe.get_app_path("quality_itagqatar"))
		out_dir = os.path.join(app_root, ".fb", "features", "f005-form-prefill-mapper")
		os.makedirs(out_dir, exist_ok=True)
		out_path = os.path.join(out_dir, "introspect-output.md")
		with open(out_path, "w") as f:
			f.write(output)
		print(f"\nWrote: {out_path}")

	return output
