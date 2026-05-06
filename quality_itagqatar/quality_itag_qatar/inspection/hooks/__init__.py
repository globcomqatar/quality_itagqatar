import importlib

import frappe


def run_hook(inspection_form, hook_type, qi_name, report):
    """Run optional per-form hook. No-op if the module or function does not exist.

    To add hooks for a form, create:
        inspection/hooks/{frappe.scrub(form_name)}.py
    with functions before_create(qi_name, report) and/or after_create(qi_name, report).
    """
    module_name = frappe.scrub(inspection_form)
    try:
        mod = importlib.import_module(
            f"quality_itagqatar.quality_itag_qatar.inspection.hooks.{module_name}"
        )
        fn = getattr(mod, hook_type, None)
        if fn:
            return fn(qi_name, report)
    except ImportError:
        pass
    return None
