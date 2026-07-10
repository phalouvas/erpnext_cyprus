# Copyright (c) 2025, KAINOTOMO PH LTD and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, today, add_months

from erpnext_cyprus.erpnext_cyprus.report.cyprus_vies_return.cyprus_vies_return import (
	execute,
	get_data,
	get_columns,
)
from erpnext_cyprus.erpnext_cyprus.tests.fixtures import (
	build_company,
	build_customer,
	build_sales_invoice,
	build_account,
	build_cost_center,
	get_company_abbr,
)


class TestCyprusViesReturn(FrappeTestCase):
	"""Test suite for Cyprus VIES Return report."""

	def setUp(self):
		self.company = build_company("_Test Cyprus VIES Co", "TCVC")
		self.abbr = get_company_abbr(self.company)

		self.income_account = build_account(self.company, self.abbr, "Sales", "Income")
		self.debtor_account = build_account(
			self.company, self.abbr, "Debtors", "Receivable", account_type="Receivable"
		)
		self.cost_center = build_cost_center(self.company, self.abbr, "Main")
		frappe.db.set_value("Company", self.company, "default_receivable_account", self.debtor_account)
		frappe.db.set_value("Company", self.company, "default_income_account", self.income_account)

		# Customers
		self.eu_de = build_customer("VIES DE Cust", "Germany", tax_id="DE123456789")
		self.eu_fr = build_customer("VIES FR Cust", "France", tax_id="FR12345678901")
		self.eu_no_addr = build_customer("VIES DE NoAddr", "Germany", tax_id="DE987654321", has_address=False)
		self.eu_no_taxid = build_customer("VIES NoTaxID", "Germany", tax_id="")
		self.non_eu = build_customer("VIES US Cust", "United States", tax_id="US12345")

		self.de_addr = frappe.db.get_value("Address", {"address_title": "VIES DE Cust-Addr"}, "name")
		self.fr_addr = frappe.db.get_value("Address", {"address_title": "VIES FR Cust-Addr"}, "name")

		si_kw = dict(
			company=self.company, posting_date=today(),
			income_account=self.income_account,
			debtor_account=self.debtor_account,
			cost_center=self.cost_center,
		)
		self._created_invoices = []

		# Included: zero-tax EU customers with tax IDs
		for cust, net, addr in [
			(self.eu_de, 1000, self.de_addr),
			(self.eu_de, 500, self.de_addr),
			(self.eu_fr, 2000, self.fr_addr),
			(self.eu_no_addr, 750, None),
		]:
			self._created_invoices.append(
				build_sales_invoice(customer=cust, net_total=net, customer_address=addr, **si_kw)
			)

		# Excluded: no tax ID
		self._created_invoices.append(
			build_sales_invoice(customer=self.eu_no_taxid, net_total=500, **si_kw)
		)
		# Excluded: non-EU
		self._created_invoices.append(
			build_sales_invoice(customer=self.non_eu, net_total=3000, **si_kw)
		)
		# Excluded: taxed
		name = build_sales_invoice(customer=self.eu_de, net_total=1000, customer_address=self.de_addr, **si_kw)
		frappe.db.set_value("Sales Invoice", name, "total_taxes_and_charges", 190)
		self._created_invoices.append(name)
		# Excluded: draft
		self._created_invoices.append(
			build_sales_invoice(customer=self.eu_de, net_total=600, customer_address=self.de_addr, do_not_submit=True, **si_kw)
		)

	def tearDown(self):
		for name in getattr(self, "_created_invoices", [])[::-1]:
			try:
				d = frappe.get_doc("Sales Invoice", name)
				if d.docstatus == 1:
					d.cancel()
				frappe.delete_doc("Sales Invoice", name, force=True)
			except Exception:
				pass
		for c in ["VIES DE Cust", "VIES FR Cust", "VIES DE NoAddr", "VIES NoTaxID", "VIES US Cust"]:
			try:
				frappe.delete_doc("Customer", c, force=True)
			except Exception:
				pass
		try:
			frappe.delete_doc("Company", self.company, force=True)
		except Exception:
			pass

	def _data(self):
		return get_data({
			"company": self.company,
			"date_range": [add_months(today(), -1), today()],
		})

	def test_columns(self):
		cols = get_columns()
		self.assertIn("customer", [c["fieldname"] for c in cols])
		self.assertIn("country", [c["fieldname"] for c in cols])
		self.assertIn("rounded_net_total", [c["fieldname"] for c in cols])

	def test_includes_zero_tax_eu_customer(self):
		self.assertIn(self.eu_de, [r["customer"] for r in self._data()])

	def test_excludes_no_tax_id(self):
		self.assertNotIn(self.eu_no_taxid, [r["customer"] for r in self._data()])

	def test_excludes_non_eu(self):
		self.assertNotIn(self.non_eu, [r["customer"] for r in self._data()])

	def test_excludes_taxed_invoices(self):
		row = next((r for r in self._data() if r["customer"] == self.eu_de), None)
		self.assertIsNotNone(row)
		self.assertAlmostEqual(flt(row["net_total"]), 1500.0, delta=0.01)

	def test_excludes_draft(self):
		row = next((r for r in self._data() if r["customer"] == self.eu_de), None)
		self.assertAlmostEqual(flt(row["net_total"]), 1500.0, delta=0.01)

	def test_aggregates_multiple_invoices(self):
		rows = [r for r in self._data() if r["customer"] == self.eu_de]
		self.assertEqual(len(rows), 1)
		self.assertAlmostEqual(flt(rows[0]["net_total"]), 1500.0, delta=0.01)

	def test_rounded_total(self):
		row = next((r for r in self._data() if r["customer"] == self.eu_de), None)
		if row:
			self.assertAlmostEqual(flt(row["rounded_net_total"]), 1500.0, delta=0.01)

	def test_separates_countries(self):
		countries = {r["country"] for r in self._data()}
		self.assertIn("Germany", countries)
		self.assertIn("France", countries)

	def test_excludes_without_customer_address(self):
		"""Customer without customer_address on the invoice is excluded (country cannot be determined)."""
		self.assertNotIn(self.eu_no_addr, [r["customer"] for r in self._data()])

	def test_empty_on_missing_filters(self):
		self.assertEqual(get_data({}), [])
		self.assertEqual(get_data({"company": self.company, "date_range": None}), [])

	def test_execute_returns_columns_and_data(self):
		cols, data = execute({
			"company": self.company,
			"date_range": [add_months(today(), -1), today()],
		})
		self.assertIsInstance(cols, list)
		self.assertIsInstance(data, list)
		self.assertGreater(len(cols), 0)
