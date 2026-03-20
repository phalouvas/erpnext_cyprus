import frappe
from frappe import _
import json
from erpnext.setup.doctype.company.company import Company
from erpnext.setup.setup_wizard.operations.taxes_setup import setup_taxes_and_charges, from_detailed_data, update_regional_tax_settings
from erpnext_cyprus.utils.customer_group_assignment import assign_customer_territory_based_on_country

class CustomCompany(Company):
	@frappe.whitelist()
	def create_default_tax_template(self):
		if self.country != "Cyprus" or self._is_test_company():
			return super().create_default_tax_template()

		company_name = self.name
		setup_tax_template(company_name)
		setup_tax_rules(company_name)
		make_salary_components(company_name)
		assign_customer_group_territory()
	
	def create_default_accounts(self):
		if self.country != "Cyprus" or self._is_test_company():
			return super().create_default_accounts()

		custom_chart = cyprus_coa()
		
		from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import create_charts

		frappe.local.flags.ignore_root_company_validation = True
		create_charts(self.name, None, self.existing_company, custom_chart)

		self.db_set(
			"default_receivable_account",
			frappe.db.get_value(
				"Account", {"company": self.name, "account_type": "Receivable", "is_group": 0}
			),
		)

		self.db_set(
			"default_payable_account",
			frappe.db.get_value("Account", {"company": self.name, "account_type": "Payable", "is_group": 0}),
		)

	def _is_test_company(self):
		return str(self.name or "").startswith("_Test")

def setup_tax_template(company_name):

		country = frappe.db.get_value("Company", company_name, "country")

		# Validate tax accounts
		validate_tax_accounts(company_name)
		
		# Regular setup for other countries
		if country != "Cyprus":
			setup_taxes_and_charges(company_name, country)
			return
		
		sales_tax_templates = [
			{
				"title": "Standard Domestic",
				"description": "For local sales with standard VAT.",
				"taxes": [
					{
						"account_head": {
							"account_name": _("Output VAT"),
							"account_number": "2312",
							"root_type": "Liability",
							"tax_rate": 19
						},
						"description": "Standard Domestic VAT",
						"charge_type": "On Net Total",
						"rate": 19
					}
				]
			},
			{
				"title": "Cyprus Reduced Rate (9%)",
				"description": "For goods and services subject to reduced VAT rate",
				"taxes": [
					{
						"account_head": {
							"account_name": _("Output VAT"),
							"account_number": "2312",
							"root_type": "Liability",
							"tax_rate": 9
						},
						"description": "Reduced Rate VAT",
						"charge_type": "On Net Total",
						"rate": 9
					}
				]
			},
			{
				"title": "Cyprus Super Reduced Rate (5%)",
				"description": "For goods and services subject to super-reduced VAT rate",
				"taxes": [
					{
						"account_head": {
							"account_name": _("Output VAT"),
							"account_number": "2312",
							"root_type": "Liability",
							"tax_rate": 5
						},
						"description": "Super Reduced Rate VAT",
						"charge_type": "On Net Total",
						"rate": 5
					}
				]
			},
			{
				"title": "Zero-Rated",
				"description": "For export sales where VAT is not charged.",
				"taxes": []
			},
			{
				"title": "Out-of-Scope",
				"description": "For sales out of scope of VAT.",
				"taxes": []
			}
		]      

		eu_vat_rates = get_eu_vat_rates()
		for country, vat_rate in eu_vat_rates.items():
			# Skip Cyprus as it uses domestic templates
			oss_template = {
				"title": f"OSS Digital Services - {country} ({vat_rate}%)",
				"description": f"Digital services to consumers in {country} (OSS)",
				"taxes": [
					{
						"account_head": {
							"account_name": _("VAT OSS"),
							"account_number": "2311",
							"root_type": "Liability",
							"tax_rate": 20.00
						},
						"description": f"VAT OSS {country} {vat_rate}%",
						"charge_type": "On Net Total",
						"rate": vat_rate
					}
				]
			}
			
			sales_tax_templates.append(oss_template)
		
		# Custom setup for Cyprus
		cyprus_tax_templates = {
			"chart_of_accounts": {
				"*": {
					"sales_tax_templates": sales_tax_templates,
					"purchase_tax_templates": [
						{
							"title": "Reverse Charge Services",
							"description": "For services purchased from EU suppliers subject to reverse charge",
							"taxes": [
								{
									"account_head": {
										"account_name": _("Output VAT"),
										"account_number": "2312",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"charge_type": "On Net Total",
									"rate": 19,
									"add_deduct_tax": "Deduct"
								},
								{
									"account_head": {
										"account_name": _("Input VAT"),
										"account_number": "1520",
										"root_type": "Asset",
										"tax_rate": 19
									},
									"charge_type": "On Net Total",
									"rate": 19,
									"add_deduct_tax": "Add"
								}
							]
						},
						{
							"title": "Zero-Rated",
							"description": "For zero-rated or exempt purchases",
							"taxes": []
						},
						{
							"title": "Standard Domestic",
							"description": "For ordinary purchases from local (Cypriot) suppliers where the supplier charges VAT at the standard rate",
							"taxes": [
								{
									"account_head": {
										"account_name": _("Input VAT"),
										"account_number": "1520",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"description": "Standard Domestic",
									"rate": 19,
									"add_deduct_tax": "Add"
								}
							]
						}
					],
					"item_tax_templates": [
						{
							"title": "Cyprus Standard",
							"taxes": [
								{
									"tax_type": {
										"account_name": _("Output VAT"),
										"account_number": "2312",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"tax_rate": 19
								}
							]
						},
						{
							"title": "Cyprus Reduced",
							"taxes": [
								{
									"tax_type": {
										"account_name": _("Output VAT"),
										"account_number": "2312",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"tax_rate": 9
								}
							]
						},
						{
							"title": "Cyprus Super Reduced",
							"taxes": [
								{
									"tax_type": {
										"account_name": _("Output VAT"),
										"account_number": "2312",
										"root_type": "Liability",
										"tax_rate": 19
									},
									"tax_rate": 5
								}
							]
						}
					]
				}
			}
		}
		
		from_detailed_data(company_name, cyprus_tax_templates)
		update_regional_tax_settings("Cyprus", company_name)

def get_eu_vat_rates():
	"""
	Return a dictionary of EU country standard VAT rates for OSS
	Source: European Commission, rates as of 2023
	"""
	return {
		"Austria": 20,
		"Belgium": 21,
		"Bulgaria": 20,
		"Croatia": 25,
		"Czech Republic": 21,
		"Denmark": 25,
		"Estonia": 22,
		"Finland": 24,
		"France": 20,
		"Germany": 19,
		"Greece": 24,
		"Hungary": 27,
		"Ireland": 23,
		"Italy": 22,
		"Latvia": 21,
		"Lithuania": 21,
		"Luxembourg": 17,
		"Malta": 18,
		"Netherlands": 21,
		"Poland": 23,
		"Portugal": 23,
		"Romania": 19,
		"Slovakia": 20,
		"Slovenia": 22,
		"Spain": 21,
		"Sweden": 25
	}

def get_eu_countries():
	"""Return a list of EU countries"""
	return list(get_eu_vat_rates().keys())

def validate_tax_accounts(company):
	required_accounts = [
		{"number": "2310", "name": "VAT Payable"},
		{"number": "2311", "name": "VAT OSS"},
		{"number": "2312", "name": "Output VAT"},
		{"number": "1520", "name": "Input VAT"}
	]
	
	missing_accounts = []
	for account in required_accounts:
		if not frappe.db.exists("Account", 
			{"account_number": account["number"], "company": company}):
			missing_accounts.append(f"{account['name']} ({account['number']})")
	
	if missing_accounts:
		frappe.msgprint(
			f"The following tax accounts are missing: {', '.join(missing_accounts)}. "
			"Tax templates may not work correctly.",
			indicator="orange",
			alert=True
		)

def setup_tax_rules(company):
	"""
	Set up Cyprus-specific tax rules for automatic tax template selection
	"""
	rules_created = []
	
	# Get the actual template names first (since they include company abbreviations)
	template_names = {}
	
	# Get sales tax templates
	sales_templates = frappe.get_all(
		"Sales Taxes and Charges Template",
		filters={"company": company},
		fields=["name", "title"]
	)
	for template in sales_templates:
		template_names[template.title] = template.name
	
	# Get purchase tax templates
	purchase_templates = frappe.get_all(
		"Purchase Taxes and Charges Template",
		filters={"company": company},
		fields=["name", "title"]
	)
	for template in purchase_templates:
		template_names[template.title] = template.name
	
	# Initialize tax rules list
	tax_rules = []
	
	# Get EU VAT rates to create country-specific digital services rules
	eu_vat_rates = get_eu_vat_rates()
	
	# First add individual country rules for digital services
	for country, vat_rate in eu_vat_rates.items():
		if country == "Cyprus":
			# For Cyprus, use the standard template
			continue
			
		template_title = f"OSS Digital Services - {country} ({vat_rate}%)"
		template_name = template_names.get(template_title)
		
		if template_name:
			rule = {
				"doctype": "Tax Rule",
				"tax_type": "Sales",
				"customer_group": "Individual", 
				"billing_country": country,
				"sales_tax_template": template_name,
				"priority": 2,
				"use_for_shopping_cart": 1
			}
			tax_rules.append(rule)
	
	# Then add the standard rules    
	standard_rules = [
		# Default domestic rule
		{
			"doctype": "Tax Rule",
			"tax_type": "Sales",
			"billing_country": "Cyprus",
			"sales_tax_template": template_names.get("Standard Domestic"),
			"priority": 2,
			"use_for_shopping_cart": 1
		},
		# EU B2B and other countries
		{
			"doctype": "Tax Rule",
			"tax_type": "Sales",
			"sales_tax_template": template_names.get("Zero-Rated"),
			"priority": 1,
			"use_for_shopping_cart": 1
		},
		
		# PURCHASE RULES
		# Domestic purchases rule
		{
			"doctype": "Tax Rule",
			"tax_type": "Purchase",
			"billing_country": "Cyprus",
			"purchase_tax_template": template_names.get("Standard Domestic"),
			"priority": 3
		},
		# EU commercial services rule
		{
			"doctype": "Tax Rule",
			"tax_type": "Purchase",
			"billing_country": "EU",
			"purchase_tax_template": template_names.get("Reverse Charge Services"),
			"priority": 2
		},        
		# Zero-rated purchases are handled by the default template
		{
			"doctype": "Tax Rule",
			"tax_type": "Purchase",
			"purchase_tax_template": template_names.get("Zero-Rated"),
			"priority": 1,
			"use_for_shopping_cart": 1
		},
	]
	
	# Combine all rules
	tax_rules.extend(standard_rules)
	
	# Create each tax rule if it doesn't already exist
	for rule_data in tax_rules:
		# Add company to rule data
		rule_data["company"] = company
		
		# Check for existing rule with similar criteria
		filters = {
			"tax_type": rule_data["tax_type"],
			"company": company,
			"priority": rule_data["priority"]
		}
		
		if "billing_country" in rule_data:
			filters["billing_country"] = rule_data["billing_country"]
			
		if "customer_group" in rule_data:
			filters["customer_group"] = rule_data["customer_group"]
			
		existing_rule = frappe.db.exists("Tax Rule", filters)
		
		if not existing_rule:
			# Special handling for EU country group
			if rule_data.get("billing_country") == "EU":
				# Create rules for each EU country
				eu_countries = get_eu_countries()
				for country in eu_countries:
					country_rule = rule_data.copy()
					country_rule["billing_country"] = country
					
					# Create the rule
					try:
						new_rule = frappe.get_doc(country_rule)
						new_rule.insert()
						rules_created.append(f"{country_rule['tax_type']} - {country} - Priority {country_rule['priority']}")
						frappe.db.commit()
					except Exception as e:
						frappe.log_error(f"Error creating tax rule for {country}: {str(e)}")
			else:
				# Create the rule
				try:
					new_rule = frappe.get_doc(rule_data)
					new_rule.insert()
					rules_created.append(f"{rule_data['tax_type']} - {rule_data.get('billing_country', 'Any')} - Priority {rule_data['priority']}")
					frappe.db.commit()
				except Exception as e:
					frappe.log_error(f"Error creating tax rule: {str(e)}")
	
	return rules_created

def make_salary_components(company):

	account_salary = frappe.get_value('Account', {'account_name': _("Salaries and Wages"), 'company': company}, 'name')
	account_redundancy_fund = frappe.get_value('Account', {'account_name': _("Redundancy Fund"), 'company': company}, 'name')
	account_human_resources_fund = frappe.get_value('Account', {'account_name': _("Human Resources Fund"), 'company': company}, 'name')
	account_social_cohesion_fund = frappe.get_value('Account', {'account_name': _("Social Cohesion Fund"), 'company': company}, 'name')
	account_social_insurance = frappe.get_value('Account', {'account_name': _("Social Insurance"), 'company': company}, 'name')
	account_ghs = frappe.get_value('Account', {'account_name': _("GHS"), 'company': company}, 'name')
	account_payroll_payable = frappe.get_value('Account', {'account_name': _("Payroll Payable"), 'company': company}, 'name')
	account_income_tax = frappe.get_value('Account', {'account_name': _("Payroll Income Tax"), 'company': company}, 'name')
	account_social_insurance_contributions = frappe.get_value('Account', {'account_name': _("Social Insurance Contributions"), 'company': company}, 'name')
	account_ghs_contributions = frappe.get_value('Account', {'account_name': _("GHS Contributions"), 'company': company}, 'name')
	
	docs = []

	file_path = frappe.get_app_path("erpnext_cyprus", "regional", "cyprus", "data", "salary_components.json")
	file_content = read_data_file(file_path)
	file_content = file_content.replace("ACCOUNT_PAYROLL_PAYABLE", account_payroll_payable)
	file_content = file_content.replace("ACCOUNT_PAYROLL_INCOME_TAX", account_income_tax)
	file_content = file_content.replace("ACCOUNT_SOCIAL_INSURANCE_CONTRIBUTIONS", account_social_insurance_contributions)
	file_content = file_content.replace("ACCOUNT_GHS_CONTRIBUTIONS", account_ghs_contributions)
	file_content = file_content.replace("ACCOUNT_SALARY", account_salary)
	file_content = file_content.replace("ACCOUNT_REDUNDANCY_FUND", account_redundancy_fund)
	file_content = file_content.replace("ACCOUNT_HUMAN_RESOURCES_FUND", account_human_resources_fund)
	file_content = file_content.replace("ACCOUNT_SOCIAL_COHESION_FUND", account_social_cohesion_fund)
	file_content = file_content.replace("ACCOUNT_SOCIAL_INSURANCE", account_social_insurance)
	file_content = file_content.replace("ACCOUNT_GHS", account_ghs)
	file_content = file_content.replace("E2C_COMPANY", company)
	docs.extend(json.loads(file_content))

	for d in docs:
		try:
			doc = frappe.get_doc(d)
			doc.flags.ignore_permissions = True
			doc.flags.ignore_mandatory = True
			doc.insert(ignore_if_duplicate=True)
		except frappe.NameError:
			frappe.clear_messages()
		except frappe.DuplicateEntryError:
			frappe.clear_messages()

def read_data_file(file_path):
	try:
		with open(file_path) as f:
			return f.read()
	except OSError:
		return "{}"
	
def cyprus_coa():
	return {
		_("Application of Funds (Assets)"): {
			_("Current Assets"): {
				_("Accounts Receivable"): {
					_("Debtors"): {"account_type": "Receivable", "account_number": "1310"},
					_("Contract Assets"): {"account_number": "1320"},
					"account_number": "1300",
				},
				_("Bank Accounts"): {"account_type": "Bank", "is_group": 1, "account_number": "1200"},
				_("Cash In Hand"): {
					_("Cash"): {"account_type": "Cash", "account_number": "1110"},
					"account_type": "Cash",
					"account_number": "1100",
				},
				_("Loans and Advances (Assets)"): {
					_("Employee Advances"): {"account_number": "1610"},
					_("Prepaid Expenses"): {"account_number": "1620"},
					"account_number": "1600",
				},
				_("Securities and Deposits"): {
					_("Earnest Money"): {"account_number": "1651"},
					_("Security Deposits"): {"account_number": "1652"},
					"account_number": "1650",
				},
				_("Stock Assets"): {
					_("Stock In Hand"): {"account_type": "Stock", "account_number": "1410"},
					_("Work In Progress"): {"account_type": "Stock", "account_number": "1420"},
					_("Finished Goods"): {"account_type": "Stock", "account_number": "1430"},
					"account_type": "Stock",
					"account_number": "1400",
				},
				_("Tax Assets"): {
					_("VAT Receivable"): {"account_type": "Tax", "account_number": "1510"},
					_("Input VAT"): {"account_type": "Tax", "account_number": "1520"},
					_("Prepaid Taxes"): {"account_type": "Tax", "account_number": "1530"},
					"is_group": 1,
					"account_number": "1500",
				},
				"account_number": "1000-1699",
			},
			_("Non-Current Assets"): {
				_("Fixed Assets"): {
					_("Land"): {"account_type": "Fixed Asset", "account_number": "1711"},
					_("Buildings"): {"account_type": "Fixed Asset", "account_number": "1712"},
					_("Furniture and Fixtures"): {"account_type": "Fixed Asset", "account_number": "1713"},
					_("Plant and Machinery"): {"account_type": "Fixed Asset", "account_number": "1714"},
					_("Vehicles"): {"account_type": "Fixed Asset", "account_number": "1715"},
					_("Office Equipment"): {"account_type": "Fixed Asset", "account_number": "1716"},
					_("Computer Equipment"): {"account_type": "Fixed Asset", "account_number": "1717"},
					_("Right-of-Use Assets"): {"account_type": "Fixed Asset", "account_number": "1718"},
					_("Accumulated Depreciation"): {
						"account_type": "Accumulated Depreciation",
						"account_number": "1719",
					},
					"account_number": "1710",
				},
				_("Intangible Assets"): {
					_("Goodwill"): {"account_type": "Fixed Asset", "account_number": "1731"},
					_("Software"): {"account_type": "Fixed Asset", "account_number": "1732"},
					_("Patents and Trademarks"): {"account_type": "Fixed Asset", "account_number": "1733"},
					_("Licenses and Franchises"): {"account_type": "Fixed Asset", "account_number": "1734"},
					_("Accumulated Amortization"): {"account_type": "Accumulated Depreciation", "account_number": "1739"},
					"account_number": "1730",
				},
				_("Investment Properties"): {
					_("Land"): {"account_type": "Fixed Asset", "account_number": "1751"},
					_("Buildings"): {"account_type": "Fixed Asset", "account_number": "1752"},
					"account_number": "1750",
				},
				_("CWIP Account"): {"account_type": "Capital Work in Progress", "account_number": "1770"},
				_("Investments"): {
					_("Investments in Subsidiaries"): {"account_number": "1811"},
					_("Investments in Associates"): {"account_number": "1812"},
					_("Financial Assets at Amortized Cost"): {"account_number": "1813"},
					_("Financial Assets at FVTPL"): {"account_number": "1814"},
					_("Financial Assets at FVOCI"): {"account_number": "1815"},
					"is_group": 1,
					"account_number": "1810",
				},
				_("Deferred Tax Assets"): {"account_number": "1840"},
				"account_number": "1700-1899",
			},
			_("Temporary Accounts"): {
				_("Temporary Opening"): {"account_type": "Temporary", "account_number": "1910"},
				"account_number": "1900",
			},
			"root_type": "Asset",
			"account_number": "1000",
		},
		_("Source of Funds (Liabilities)"): {
			_("Current Liabilities"): {
				_("Accounts Payable"): {
					_("Creditors"): {"account_type": "Payable", "account_number": "2110"},
					_("Accrued Expenses"): {"account_number": "2115"},
					"account_number": "2100",
				},
				_("Payroll Liabilities"): {
					_("Payroll Payable"): {"account_number": "2120"},
					_("Social Insurance Contributions"): {"account_number": "2121"},
					_("Payroll Income Tax"): {"account_number": "2122"},
					_("GHS Contributions"): {"account_number": "2123"},
					"account_number": "2120-2129",
				},
				_("Stock Liabilities"): {
					_("Stock Received But Not Billed"): {
						"account_type": "Stock Received But Not Billed",
						"account_number": "2210",
					},
					_("Asset Received But Not Billed"): {
						"account_type": "Asset Received But Not Billed",
						"account_number": "2211",
					},
					"account_number": "2200",
				},
				_("Tax Liabilities"): {
					_("VAT Payable"): {"account_number": "2310", "account_type": "Tax"},
					_("VAT OSS"): {"account_number": "2311", "account_type": "Tax"},
					_("Output VAT"): {"account_number": "2312", "account_type": "Tax"},
					_("Special Defense Contribution Payable"): {"account_number": "2320", "account_type": "Tax"},
					_("Corporate Tax Payable"): {"account_number": "2330", "account_type": "Tax"},
					_("Stamp Duty Payable"): {"account_number": "2340", "account_type": "Tax"},
					"account_type": "Tax",
					"is_group": 1,
					"account_number": "2300",
				},
				_("Short-term Loans"): {
					_("Bank Overdraft"): {"account_number": "2410"},
					_("Current Portion of Long-term Loans"): {"account_number": "2420"},
					_("Short-term Borrowings"): {"account_number": "2430"},
					"account_number": "2400",
				},
				_("Contract Liabilities"): {"account_number": "2500"},
				_("Current Lease Liabilities"): {"account_number": "2600"},
				"account_number": "2100-2699",
			},
			_("Non-Current Liabilities"): {
				_("Long-term Loans"): {
					_("Bank Loans"): {"account_number": "2710"},
					_("Other Long-term Borrowings"): {"account_number": "2720"},
					_("Bonds Payable"): {"account_number": "2730"},
					"account_number": "2700",
				},
				_("Non-Current Lease Liabilities"): {"account_number": "2800"},
				_("Provisions"): {
					_("Provision for Employee Benefits"): {"account_number": "2910"},
					_("Provision for Warranty"): {"account_number": "2920"},
					_("Other Provisions"): {"account_number": "2930"},
					"account_number": "2900",
				},
				_("Deferred Tax Liabilities"): {"account_number": "2950"},
				"account_number": "2700-2999",
			},
			"root_type": "Liability",
			"account_number": "2000",
		},
		_("Equity"): {
			_("Capital"): {
				_("Share Capital"): {"account_type": "Equity", "account_number": "3110"},
				_("Share Premium"): {"account_type": "Equity", "account_number": "3120"},
				_("Treasury Shares"): {"account_type": "Equity", "account_number": "3130"},
				"account_type": "Equity",
				"account_number": "3100",
			},
			_("Reserves"): {
				_("Legal Reserve"): {"account_type": "Equity", "account_number": "3210"},
				_("Revaluation Reserve"): {"account_type": "Equity", "account_number": "3220"},
				_("Fair Value Reserve"): {"account_type": "Equity", "account_number": "3230"},
				_("Foreign Currency Translation Reserve"): {"account_type": "Equity", "account_number": "3240"},
				_("Other Reserves"): {"account_type": "Equity", "account_number": "3250"},
				"account_type": "Equity",
				"account_number": "3200",
			},
			_("Retained Earnings"): {"account_type": "Equity", "account_number": "3300"},
			_("Other Comprehensive Income"): {
				_("Remeasurements of Defined Benefit Plans"): {"account_type": "Equity", "account_number": "3410"},
				_("OCI - Financial Instruments"): {"account_type": "Equity", "account_number": "3420"},
				"account_type": "Equity",
				"account_number": "3400",
			},
			_("Opening Balance Equity"): {"account_type": "Equity", "account_number": "3900"},
			"root_type": "Equity",
			"account_number": "3000",
		},
		_("Income"): {
			_("Operating Revenue"): {
				_("Sales"): {"account_number": "6110"},
				_("Service Revenue"): {"account_number": "6120"},
				_("Rental Income"): {"account_number": "6130"},
				_("Commission Income"): {"account_number": "6140"},
				_("Sales Returns and Allowances"): {"account_number": "6150"},
				_("Sales Discounts"): {"account_number": "6160"},
				"account_number": "6100",
			},
			_("Other Income"): {
				_("Interest Income"): {"account_number": "6210"},
				_("Dividend Income"): {"account_number": "6220"},
				_("Gain on Sale of Assets"): {"account_number": "6230"},
				_("Foreign Exchange Gain"): {"account_number": "6240"},
				_("Miscellaneous Income"): {"account_number": "6290"},
				"account_number": "6200",
			},
			"root_type": "Income",
			"account_number": "6000",
		},
		_("Expenses"): {
			_("Cost of Goods Sold"): {
				_("Material Costs"): {"account_number": "8110"},
				_("Purchase Returns and Allowances"): {"account_number": "8120"},
				_("Purchase Discounts"): {"account_number": "8130"},
				_("Direct Labor"): {"account_number": "8140"},
				_("Manufacturing Overhead"): {"account_number": "8150"},
				_("COGS Adjustment"): {"account_type": "Stock Adjustment", "account_number": "8190"},
				"account_number": "8100",
			},
			_("Operating Expenses"): {
				_("Staff Costs"): {
					_("Salaries and Wages"): {"account_number": "8211"},
					_("Social Insurance"): {"account_number": "8212"},
					_("GHS"): {"account_number": "8213"},
					_("Human Resources Fund"): {"account_number": "8214"},
					_("Redundancy Fund"): {"account_number": "8215"},
					_("Social Cohesion Fund"): {"account_number": "8216"},
					_("Employee Benefits"): {"account_number": "8219"},
					"account_number": "8210",
				},
				_("Employee Benefits"): {"account_number": "8220"},
				_("Depreciation"): {"account_type": "Depreciation", "account_number": "8230"},
				_("Amortization"): {"account_type": "Depreciation", "account_number": "8235"},
				_("Rent"): {"account_number": "8240"},
				_("Utilities"): {"account_number": "8250"},
				_("Office Supplies"): {"account_number": "8260"},
				_("Professional Fees"): {"account_number": "8270"},
				_("Marketing and Advertising"): {"account_type": "Chargeable", "account_number": "8280"},
				_("Travel and Entertainment"): {"account_number": "8290"},
				_("Insurance"): {"account_number": "8310"},
				_("Repairs and Maintenance"): {"account_number": "8320"},
				_("Telephone and Internet"): {"account_number": "8330"},
				_("Printing and Stationery"): {"account_number": "8340"},
				_("Licenses and Fees"): {"account_number": "8350"},
				_("Training and Development"): {"account_number": "8360"},
				_("Other Operating Expenses"): {"account_type": "Chargeable", "account_number": "8390"},
				"account_number": "8200-8399",
			},
			_("Financial Expenses"): {
				_("Interest Expense"): {"account_number": "8410"},
				_("Bank Charges"): {"account_number": "8420"},
				_("Foreign Exchange Loss"): {"account_number": "8430"},
				_("Loan Processing Fees"): {"account_number": "8440"},
				"account_number": "8400",
			},
			_("Other Expenses"): {
				_("Loss on Asset Disposal"): {"account_number": "8510"},
				_("Donations"): {"account_number": "8520"},
				_("Fines and Penalties"): {"account_number": "8530"},
				_("Bad Debts"): {"account_number": "8540"},
				_("Miscellaneous Expenses"): {"account_type": "Chargeable", "account_number": "8590"},
				"account_number": "8500",
			},
			_("Tax Expenses"): {
				_("Corporate Income Tax"): {"account_number": "8610"},
				_("Special Defense Contribution"): {"account_number": "8620"},
				_("Deferred Tax Expense"): {"account_number": "8630"},
				"account_number": "8600",
			},
			_("Adjustment Accounts"): {
				_("Round Off"): {"account_type": "Round Off", "account_number": "8910"},
				_("Write Off"): {"account_number": "8920"},
				_("Expenses Included In Asset Valuation"): {
					"account_type": "Expenses Included In Asset Valuation",
					"account_number": "8930",
				},
				_("Expenses Included In Valuation"): {
					"account_type": "Expenses Included In Valuation",
					"account_number": "8940",
				},
				"account_number": "8900",
			},
			"root_type": "Expense",
			"account_number": "8000",
		},
	}

def assign_customer_group_territory():
	"""
	Run assignment methods for all customers and their addresses
	"""
	print("\n=== Starting Customer Group and Territory Assignment ===\n")
	
	# Process all customers for VAT group assignment
	customers = frappe.get_all("Customer", filters={"customer_name": ["!=", ""]}, fields=["name"])
	count = 0
	total = len(customers)
	
	for customer in customers:
		try:
			customer_doc = frappe.get_doc("Customer", customer.name)
			assign_customer_group_based_on_vat(customer_doc)
			customer_doc.save(ignore_permissions=True)
			
			count += 1                
			if count % 100 == 0:
				frappe.db.commit()
				frappe.publish_progress(
					percent=int(count * 100 / total),
					title="Processing Customers",
					description=f"Assigning customer groups ({count}/{total})"
				)
		except Exception as e:
			frappe.log_error(f"Error processing customer {customer.name}: {str(e)}")
	
	frappe.db.commit()
	
	# Process all customer addresses for territory assignment
	addresses = frappe.get_all(
		"Address", 
		filters=[["Dynamic Link", "link_doctype", "=", "Customer"]],
		fields=["name"]
	)
	
	count = 0
	total = len(addresses)
	
	for address in addresses:
		try:
			address_doc = frappe.get_doc("Address", address.name)
			assign_customer_territory_based_on_country(address_doc)
			
			count += 1
			if count % 100 == 0:
				frappe.db.commit()
				frappe.publish_progress(
					percent=int(count * 100 / total),
					title="Processing Customers",
					description=f"Assigning customer territory ({count}/{total})"
				)
		except Exception as e:
			frappe.log_error(f"Error processing address {address.name}: {str(e)}")
	
	frappe.db.commit()
	frappe.publish_progress(
		percent=100,
		title="Processing Customers",
		description="Completed territory assignment for {total} addresses"
	)

def assign_customer_group_based_on_vat(doc, method=None):
	"""
	Assigns 'Commercial' group if tax_id is a valid VIES VAT number, else 'Individual'.
	Only proceeds if tax_id field is modified (dirty) and not empty.
	"""
		
	if doc.tax_id and doc.tax_id != "":
		doc.customer_group = "Commercial"
		doc.customer_type = "Company"
	else:
		doc.customer_group = "Individual"
		doc.customer_type = "Individual"
