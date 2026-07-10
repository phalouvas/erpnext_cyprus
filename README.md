# ERPNext Cyprus

ERPNext extension for companies in Cyprus.

## Features

- Cyprus-specific tax compliance
- VAT reporting for Cyprus (standard VAT returns, MOSS, and VIES statements)
- Localized accounting features
- Additional reports for Cyprus regulatory requirements
- Cyprus banks integration

## Installation

```bash
bench get-app https://github.com/your-organization/erpnext_cyprus
bench --site your-site.local install-app erpnext_cyprus
```

## Requirements

- ERPNext v16

## Tax Account Setup

The app automatically configures the following tax-related components:

### Tax Accounts
- **VAT** - Standard account for Cyprus VAT operations
- **OSS VAT** - For Mini One Stop Shop reporting for B2C digital services

### Account Structure
- VAT accounts use account number 2320 under Liabilities
- OSS VAT accounts are organized by country for reporting compliance

### Tax Templates
- **Purchase Tax Templates**: 
  - Reverse Charge (implemented as a double-entry with 19% VAT added and deducted in the same transaction)
  - Standard Domestic (19% VAT)
  - Zero-Rated (for exempt purchases)

- **Sales Tax Templates**:
  - Standard Domestic (19% VAT)
  - Zero-Rated (for exports)
  - Out-of-Scope (for non-VAT sales)
  - OSS templates for each EU country with country-specific VAT rates

- **Item Tax Templates**:
  - Cyprus Standard 19%
  - Cyprus Reduced 9%
  - Cyprus Super Reduced 5%
  - Zero Rated
  - Exempt

### Tax Rules
Automatically applies correct tax templates based on:
- Customer/supplier country
- Whether the transaction is B2B or B2C
- Type of goods/services
- Rules are applied according to priority levels (higher numbers take precedence)
- Specific country rules take precedence over generic rules

### Service Items
- Any product that is not a tangible product should be marked as "Is Service" in order

- Any product that is not a tangible product should be marked as "Is Service" in order to be properly categorized in VAT returns (boxes 8A/8B for sales and 11A/11B for purchases)

## Documentation

Available documentation:

- [Cyprus VAT Return Guide](documentation/cyprus_vat_return.md) - How to prepare and submit Cyprus VAT returns
- [MOSS VAT Returns Guide](documentation/moss_vat_returns.md) - Guide for Mini One Stop Shop VAT reporting for digital services
- [VIES Statement Guide](documentation/vies_statement.md) - How to properly record and report EU B2B transactions
- [Banks integration](documentation/banks_integration.md) - How to integrate Cyprus banks

## Payroll Setup

The app automatically configures Cyprus-specific payroll components:

- **Employer Contributions**:
  - Social Insurance (8.8%, capped at €5,551 per month)
  - Redundancy Fund (1.2%, capped at €5,551 per month)
  - Human Resource Fund (0.5%, capped at €5,551 per month)
  - Social Cohesion Fund (2.0%, uncapped)
  - GESY (General Health System) (2.9%, uncapped)

- **Employee Deductions**:
  - Social Insurance (8.8%, capped at €5,551 per month)
  - GESY (2.65%, uncapped)
  - Income Tax (calculated according to Cyprus tax brackets)

## Testing

Run all tests for this app:

```bash
bench --site tmp.localhost console <<< '
import frappe, unittest
frappe.flags.test_mode = True
from erpnext_cyprus.erpnext_cyprus.report.cyprus_vies_return.test_cyprus_vies_return import TestCyprusViesReturn
suite = unittest.TestLoader().loadTestsFromTestCase(TestCyprusViesReturn)
unittest.TextTestRunner(verbosity=2).run(suite)
'
```

This runs the VIES report tests directly without triggering the ERPNext test bootstrap preloader.

## Support

For issues and feature requests, please create an issue on the [GitHub repository](https://github.com/kainotomo/erpnext_cyprus/issues).

## License

GPL-3.0