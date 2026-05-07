"""
Global config for the Job Card → Quality Reports prefill mapper.

Per-report renames live as `MAPPING_OVERRIDES` class attrs on each report
controller, NOT here. Keep this file pure constants.
"""

SAFE_FIELDTYPES = frozenset({
	"Data",
	"Link",
	"Date",
	"Datetime",
	"Float",
	"Int",
	"Select",
	"Small Text",
	"Long Text",
	"Text",
})

BLOCK_FIELDS = frozenset({
	"name",
	"naming_series",
	"docstatus",
	"idx",
	"owner",
	"creation",
	"modified",
	"modified_by",
	"parent",
	"parentfield",
	"parenttype",
	"amended_from",
})

# Walk order = priority. Each entry = (attr_on_previous_doc, next_doctype).
# Anchor = Job Card (resolved at runtime via the report's Link → Job Card field).
SOURCE_CHAIN = (
	("work_order", "Work Order"),
	("sales_order", "Sales Order"),
)
