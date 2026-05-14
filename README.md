### Change Log

## __version__ = "15.1.1"
- Inward-inspection code consolidated into this app (Stock Entry submit validator, QI inward serial-no field + JS moved out of globcom_manufacturing).

## __version__ = "15.1.0"
- "Start Inspection" flow on Stock Entry (mirrors the Job Card flow).
- Field mapping supports Stock Entry as a source, not just Job Card.
- Inspection-form dropdown options now served dynamically from app code (single source of truth).
- Naming series for Quality Field Mapping records.
- Moved Stock Entry inward-inspection field + the QI→SE auto-submit hook from globcom_manufacturing into this app.

## __version__ = "15.0.2"
- Config-driven prefill: dot-walked source paths via Quality Field Mapping, before_insert trigger, manual Refresh from Source button, audit log.

## __version__ = "15.0.1"
- Transfer Quality Forms form erpcloud_itagqatar.
- Made a unified comon field mapper for all forms.