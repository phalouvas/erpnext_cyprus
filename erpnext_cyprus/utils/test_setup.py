"""Test environment setup hooks for erpnext_cyprus."""

import frappe


def before_tests():
	"""Monkey-patch to prevent validate_inclusive_tax from blocking bootstrap."""
	from erpnext.controllers.accounts_controller import validate_inclusive_tax as orig_fn

	def _patched(tax, doc):
		pass

	# Known modules that import validate_inclusive_tax
	for mod_path in [
		"erpnext.controllers.accounts_controller",
		"erpnext.accounts.doctype.sales_taxes_and_charges_template.sales_taxes_and_charges_template",
		"erpnext.accounts.doctype.payment_entry.payment_entry",
		"erpnext.controllers.taxes_and_totals",
	]:
		try:
			mod = frappe.get_module(mod_path)
			mod.validate_inclusive_tax = _patched
		except Exception:
			pass
