# Copyright (c) 2026, Globcom Qatar and contributors
# For license information, please see license.txt

"""Mixin wiring the prefill engine into report controllers via before_insert."""

from quality_itagqatar.quality_itag_qatar.inspection.prefill import (
	TRIGGER_INSERT,
	_write_log,
	prefill_target,
)


class PrefillMixin:
	def before_insert(self):
		filled = prefill_target(self, trigger=TRIGGER_INSERT)
		if filled:
			_write_log(self, filled, TRIGGER_INSERT)
