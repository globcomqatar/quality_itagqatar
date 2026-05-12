# Copyright (c) 2026, Globcom Qatar and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class QualityFieldMapping(Document):
	def validate(self):
		self._validate_target_fields_exist()
		self._validate_no_duplicate_target_priority()

	def _validate_target_fields_exist(self):
		meta = frappe.get_meta(self.target_doctype)
		field_names = {f.fieldname for f in meta.fields}
		for rule in self.rules:
			if rule.target_field not in field_names:
				frappe.throw(
					_("Row {0}: Target field {1} not found on {2}").format(
						rule.idx, rule.target_field, self.target_doctype
					)
				)

	def _validate_no_duplicate_target_priority(self):
		seen = set()
		for rule in self.rules:
			key = (rule.target_field, rule.priority)
			if key in seen:
				frappe.throw(
					_("Row {0}: duplicate (target_field, priority) for {1} @ priority {2}").format(
						rule.idx, rule.target_field, rule.priority
					)
				)
			seen.add(key)
