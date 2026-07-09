# Copyright (c) 2025, KAINOTOMO PH LTD and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, today, add_months, getdate
from erpnext_cyprus.erpnext_cyprus.report.cyprus_vat_return.cyprus_vat_return import (
	get_reverse_charge_tax_amount,
	get_fallback_vat_rate,
	get_marked_je_adjustments,
	get_reverse_charge_pis_without_tax_rows,
	get_eu_pis_without_supplier_address,
	get_unmarked_je_count,
	get_box_11a,
	get_box_11b,
)


class TestCyprusVatReturn(FrappeTestCase):
	"""Test suite for Cyprus VAT Return reverse charge reliability."""

	def setUp(self):
		"""Create test data: company, accounts, tax template, and purchase invoices."""
		# Create or get test company
		self.company = self._create_test_company()
		self.company_abbr = frappe.db.get_value("Company", self.company, "abbr")
		
		# Create or get VAT accounts
		self.output_vat_account = self._create_account("Output VAT Test", "2312", "Liability")
		self.input_vat_account = self._create_account("Input VAT Test", "1520", "Asset")
		
		# Create or get reverse charge tax template master
		self.template_name = f"Reverse Charge Services - {self.company_abbr}"
		self._create_reverse_charge_template()
		
		# Create EU supplier with proper address
		self.eu_supplier = self._create_supplier("Test EU Supplier", "Greece", has_address=True)
		
		# Create domestic supplier
		self.domestic_supplier = self._create_supplier("Test Domestic Supplier", "Cyprus", has_address=True)
		
		# Create EU supplier WITHOUT address (for diagnostic tests)
		self.eu_supplier_no_addr = self._create_supplier("Test EU Supplier No Addr", "Greece", has_address=False)

	def tearDown(self):
		"""Clean up test data."""
		# Delete test purchase invoices
		frappe.db.delete("Purchase Invoice", {"company": self.company, "docstatus": 0})
		# Delete test suppliers
		for supplier in [self.eu_supplier, self.domestic_supplier, self.eu_supplier_no_addr]:
			if supplier:
				frappe.delete_doc("Supplier", supplier, force=True)
		# Delete test accounts
		for account in [self.output_vat_account, self.input_vat_account]:
			if account:
				frappe.delete_doc("Account", account, force=True)
		# Clean up template data
		frappe.db.delete("Purchase Taxes and Charges", {"parent": self.template_name, "parenttype": "Purchase Taxes and Charges Template"})
		
	def _create_test_company(self):
		"""Create or get a test company."""
		company_name = "Test Cyprus Company RC"
		if frappe.db.exists("Company", company_name):
			return company_name
		
		company = frappe.get_doc({
			"doctype": "Company",
			"company_name": company_name,
			"abbr": "TCRC",
			"country": "Cyprus",
			"default_currency": "EUR",
		})
		company.insert()
		return company.name

	def _create_account(self, account_name, account_number, root_type):
		"""Create or get a test account."""
		name = f"{account_name} - {self.company_abbr}"
		if frappe.db.exists("Account", name):
			return name
		
		# Get parent account based on root_type
		parent_account = frappe.db.get_value("Account", {
			"root_type": root_type,
			"company": self.company,
			"is_group": 1
		}, "name")
		
		account = frappe.get_doc({
			"doctype": "Account",
			"account_name": account_name,
			"account_number": account_number,
			"company": self.company,
			"root_type": root_type,
			"account_type": "Tax",
			"parent_account": parent_account,
			"is_group": 0,
		})
		account.insert()
		return account.name

	def _create_reverse_charge_template(self):
		"""Create a Reverse Charge purchase taxes and charges template."""
		if frappe.db.exists("Purchase Taxes and Charges Template", self.template_name):
			return
		
		template = frappe.get_doc({
			"doctype": "Purchase Taxes and Charges Template",
			"title": self.template_name,
			"company": self.company,
			"taxes": [
				{
					"charge_type": "On Net Total",
					"account_head": self.output_vat_account,
					"description": "Reverse Charge Output VAT 19%",
					"rate": 19,
					"add_deduct_tax": "Deduct",
				},
				{
					"charge_type": "On Net Total",
					"account_head": self.input_vat_account,
					"description": "Reverse Charge Input VAT 19%",
					"rate": 19,
					"add_deduct_tax": "Add",
				},
			],
		})
		template.insert()

	def _create_supplier(self, supplier_name, country, has_address=True):
		"""Create a test supplier with optional address."""
		if frappe.db.exists("Supplier", supplier_name):
			return supplier_name
		
		supplier = frappe.get_doc({
			"doctype": "Supplier",
			"supplier_name": supplier_name,
			"supplier_type": "Company",
			"country": country,
		})
		supplier.insert()
		
		if has_address and country:
			address_name = frappe.db.get_value("Address", {"address_title": f"{supplier_name}-Addr"})
			if not address_name:
				address = frappe.get_doc({
					"doctype": "Address",
					"address_title": f"{supplier_name}-Addr",
					"address_type": "Billing",
					"address_line1": "123 Test Street",
					"city": "Test City",
					"country": country,
					"links": [{"link_doctype": "Supplier", "link_name": supplier_name}],
				})
				address.insert()
				address_name = address.name
			
			# Set supplier_address on the supplier (via default address)
			supplier.db_set("supplier_primary_address", address_name)
		
		return supplier.name

	def _create_purchase_invoice(self, supplier, net_total, use_reverse_charge=True, 
								   with_tax_rows=True, posting_date=None):
		"""Create a test Purchase Invoice."""
		if posting_date is None:
			posting_date = today()
		
		pi = frappe.get_doc({
			"doctype": "Purchase Invoice",
			"company": self.company,
			"supplier": supplier,
			"posting_date": posting_date,
			"due_date": posting_date,
			"items": [
				{
					"item_code": "_Test Item",
					"qty": 1,
					"rate": net_total,
					"expense_account": frappe.db.get_value("Company", self.company, "default_expense_account"),
					"warehouse": frappe.db.get_value("Warehouse", {"company": self.company}, "name"),
				}
			],
		})
		
		if use_reverse_charge:
			pi.taxes_and_charges = self.template_name
		
		pi.insert()
		
		# Add tax rows if requested (simulates populated taxes)
		if use_reverse_charge and with_tax_rows:
			tax_amount = net_total * 19 / 100
			taxes = pi.get("taxes", [])
			taxes.append({
				"charge_type": "On Net Total",
				"account_head": self.output_vat_account,
				"description": "Reverse Charge Output VAT 19%",
				"rate": 19,
				"add_deduct_tax": "Deduct",
				"base_tax_amount": tax_amount,
			})
			taxes.append({
				"charge_type": "On Net Total",
				"account_head": self.input_vat_account,
				"description": "Reverse Charge Input VAT 19%",
				"rate": 19,
				"add_deduct_tax": "Add",
				"base_tax_amount": tax_amount,
			})
			pi.save()
		
		return pi.name

	def _create_marked_je(self, vat_account, debit=0, credit=0, marker="VAT-RC-ADJ: Test adjustment"):
		"""Create a Journal Entry with VAT-RC-ADJ marker."""
		je = frappe.get_doc({
			"doctype": "Journal Entry",
			"company": self.company,
			"posting_date": today(),
			"remark": marker,
			"accounts": [
				{
					"account": vat_account,
					"debit": debit,
					"credit": credit,
				},
				{
					"account": frappe.db.get_value("Company", self.company, "default_expense_account"),
					"debit": credit,
					"credit": debit,
				},
			],
		})
		je.insert()
		je.submit()
		return je.name

	# === Tests ===

	def test_reverse_charge_tax_primary_path(self):
		"""
		Scenario: PI with Reverse Charge template AND populated tax rows.
		Expected: get_reverse_charge_tax_amount returns correct VAT for both Add and Deduct rows.
		"""
		pi_name = self._create_purchase_invoice(
			self.eu_supplier, net_total=1000, use_reverse_charge=True, with_tax_rows=True
		)
		
		# Get Deduct (output VAT) amount
		output_vat = get_reverse_charge_tax_amount(
			self.company, add_months(today(), -1), today(), 
			self.output_vat_account, 'Deduct'
		)
		self.assertAlmostEqual(flt(output_vat), 190.0, delta=0.01, 
			msg="Deduct row should return +190 (19% of 1000, raw amount for Box 2)")
		
		# Get Add (input VAT) amount
		input_vat = get_reverse_charge_tax_amount(
			self.company, add_months(today(), -1), today(),
			self.input_vat_account, 'Add'
		)
		self.assertAlmostEqual(flt(input_vat), 190.0, delta=0.01,
			msg="Add row should return 190 (19% of 1000, positive)")

	def test_reverse_charge_empty_tax_rows(self):
		"""
		Scenario: PI with Reverse Charge template BUT empty tax rows.
		Expected: get_reverse_charge_tax_amount returns 0.
		"""
		pi_name = self._create_purchase_invoice(
			self.eu_supplier, net_total=1000, use_reverse_charge=True, with_tax_rows=False
		)
		
		output_vat = get_reverse_charge_tax_amount(
			self.company, add_months(today(), -1), today(),
			self.output_vat_account, 'Deduct'
		)
		self.assertEqual(flt(output_vat), 0,
			"Empty tax rows should result in 0 from tax rows query")

	def test_fallback_vat_rate_derived(self):
		"""
		Scenario: Company has Reverse Charge template defined.
		Expected: get_fallback_vat_rate returns the rate from the template.
		"""
		rate = get_fallback_vat_rate(self.company)
		self.assertEqual(flt(rate), 19.0,
			"Fallback rate should be 19.0 (derived from Reverse Charge template)")

	def test_fallback_vat_rate_default(self):
		"""
		Scenario: Company without Reverse Charge template.
		Expected: get_fallback_vat_rate returns default 19%.
		"""
		company_no_template = self._create_test_company()
		rate = get_fallback_vat_rate(company_no_template)
		self.assertEqual(flt(rate), 19.0,
			"Fallback rate should default to 19% when no template exists")

	def test_marked_je_adjustments_output_vat(self):
		"""
		Scenario: Marked JE posted on Output VAT account.
		Expected: get_marked_je_adjustments correctly returns debit and credit totals.
		"""
		je_name = self._create_marked_je(self.output_vat_account, debit=0, credit=100)
		
		debit, credit = get_marked_je_adjustments(
			self.company, add_months(today(), -1), today(), self.output_vat_account
		)
		self.assertEqual(flt(debit), 0)
		self.assertAlmostEqual(flt(credit), 100.0, delta=0.01)

	def test_marked_je_adjustments_input_vat(self):
		"""
		Scenario: Marked JE posted on Input VAT account.
		Expected: get_marked_je_adjustments correctly returns debit and credit totals.
		"""
		je_name = self._create_marked_je(self.input_vat_account, debit=100, credit=0)
		
		debit, credit = get_marked_je_adjustments(
			self.company, add_months(today(), -1), today(), self.input_vat_account
		)
		self.assertAlmostEqual(flt(debit), 100.0, delta=0.01)
		self.assertEqual(flt(credit), 0)

	def test_marked_je_excludes_unmarked(self):
		"""
		Scenario: JE without VAT-RC-ADJ marker on VAT account.
		Expected: get_marked_je_adjustments returns 0 (excluded).
		"""
		je_name = self._create_marked_je(
			self.output_vat_account, debit=0, credit=100, marker="Regular adjustment"
		)
		
		debit, credit = get_marked_je_adjustments(
			self.company, add_months(today(), -1), today(), self.output_vat_account
		)
		self.assertEqual(flt(debit), 0)
		self.assertEqual(flt(credit), 0,
			"Unmarked JE should be excluded")

	def test_reverse_charge_pis_without_tax_rows_detected(self):
		"""
		Scenario: PI uses Reverse Charge template but has empty tax rows.
		Expected: get_reverse_charge_pis_without_tax_rows returns count > 0.
		"""
		pi_name = self._create_purchase_invoice(
			self.eu_supplier, net_total=1000, use_reverse_charge=True, with_tax_rows=False
		)
		
		count = get_reverse_charge_pis_without_tax_rows(
			self.company, add_months(today(), -1), today()
		)
		self.assertGreater(count, 0,
			"PI with empty tax rows should be detected")

	def test_reverse_charge_pis_with_tax_rows_not_counted(self):
		"""
		Scenario: PI uses Reverse Charge template with populated tax rows.
		Expected: get_reverse_charge_pis_without_tax_rows returns 0.
		"""
		pi_name = self._create_purchase_invoice(
			self.eu_supplier, net_total=1000, use_reverse_charge=True, with_tax_rows=True
		)
		
		count = get_reverse_charge_pis_without_tax_rows(
			self.company, add_months(today(), -1), today()
		)
		self.assertEqual(count, 0,
			"PI with populated tax rows should not be flagged")

	def test_eu_pis_without_supplier_address_detected(self):
		"""
		Scenario: EU supplier PI without supplier_address.
		Expected: get_eu_pis_without_supplier_address returns count > 0.
		"""
		pi_name = self._create_purchase_invoice(
			self.eu_supplier_no_addr, net_total=1000, use_reverse_charge=True, with_tax_rows=True
		)
		
		count = get_eu_pis_without_supplier_address(
			self.company, add_months(today(), -1), today()
		)
		self.assertGreater(count, 0,
			"EU PI without supplier_address should be detected")

	def test_unmarked_je_detected(self):
		"""
		Scenario: JE on VAT account without marker.
		Expected: get_unmarked_je_count returns count > 0.
		"""
		je_name = self._create_marked_je(
			self.output_vat_account, debit=0, credit=100, marker="No marker here"
		)
		
		count = get_unmarked_je_count(
			self.company, add_months(today(), -1), today(),
			self.output_vat_account, self.input_vat_account
		)
		self.assertGreater(count, 0,
			"Unmarked JE on VAT account should be detected")
