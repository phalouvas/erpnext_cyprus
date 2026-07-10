# OSS VAT Returns Guide for Cyprus

The OSS (One Stop Shop) VAT Returns report in ERPNext Cyprus helps businesses report and pay VAT on digital services provided to consumers in other EU member states. This guide explains how to properly set up and mark transactions for accurate OSS VAT reporting.

## Table of Contents
1. [Understanding OSS](#understanding-oss)
2. [Company Configuration](#company-configuration)
3. [Tax Account Setup](#tax-account-setup)
4. [Customer Configuration](#customer-configuration)
5. [Item Setup](#item-setup)
6. [Sales Transactions](#sales-transactions)
7. [Report Interpretation](#report-interpretation)
8. [Filing Requirements](#filing-requirements)

## Understanding OSS

The OSS (One Stop Shop) is a simplified system that allows businesses supplying digital services to consumers in other EU member states to:
- Register for VAT in just one EU country (Cyprus in this case)
- Submit a single OSS VAT return and payment
- Avoid registering for VAT separately in each EU country where services are provided

The OSS replaced the earlier MOSS (Mini One Stop Shop) scheme on 1 July 2021.

The system applies to B2C (Business to Consumer) digital services, including:
- Digital content (e-books, music, games, software)
- Streaming services
- Online courses
- Website hosting and maintenance
- Access to databases

## Company Configuration

Before using OSS VAT reporting:

1. Register for the OSS scheme with the Cyprus Tax Department through the [OSS portal](https://tax-oss.mof.gov.cy)
2. Configure your company settings:
   - Ensure your company's Tax ID is properly set up with the CY prefix
   - Configure your company's default currency (EUR)
   - Set the fiscal year and quarters matching Cyprus tax calendar

## Tax Account Setup

The app automatically configures the following for OSS reporting:

1. **OSS VAT Account** (account number 2311):
   - A single "VAT OSS" account is created under Liabilities
   - Country-specific OSS sales tax templates are created for each EU member state
   - Each template is linked to the OSS VAT account with the appropriate VAT rate for that country

2. **OSS Sales Tax Templates**:
   - Named following the convention: "OSS Digital Services - [Country] ([Rate]%)"
   - Example: "OSS Digital Services - Germany (19%)"
   - These templates are automatically selected based on the customer's country for Individual customers

## Customer Configuration

Proper customer configuration is essential for OSS reporting:

1. For B2C customers in other EU member states:
   - Create customer records with country field correctly set
   - Designate them as "Individual" customers (not businesses)
   - No Tax ID is required for B2C customers

2. Customer address verification:
   - Implement systems to collect and verify customer location (at least two pieces of non-contradictory evidence):
     - Billing address
     - IP address
     - Bank location
     - Country code of SIM card
     - Fixed landline location

## Item Setup

Correctly mark items eligible for OSS reporting:

1. Go to Item master record
2. Enable "Is Digital Service" custom field (`custom_is_service`)
3. Tag items appropriately as digital services
4. Verify these items have VAT-inclusive pricing as required

## Sales Transactions

When creating sales invoices:

1. Select the correct customer with verified EU country
2. Choose items marked as digital services
3. Apply the appropriate OSS tax template for the customer's country:
   - System should suggest the correct tax based on customer's country and Individual customer group
   - Verify the tax rate matches the current rate for that country

4. For each transaction, ensure:
   - Local currency amount is calculated correctly
   - VAT is calculated at the appropriate rate for the customer's country
   - Invoice includes all required information for OSS compliance

## Report Interpretation

The OSS VAT Returns report provides per-country totals based on submitted Sales Invoices:

- **Country**: The EU member state where the customer is located
- **Net Total**: Sum of net sales amounts excluding VAT
- **Total Taxes**: Sum of VAT collected at country-specific rates
- **Tax Rate (%)**: Effective VAT rate derived from total tax divided by net total
- **Grand Total**: Total invoice amounts including VAT

### Inclusion Criteria

The report groups Sales Invoices by customer address country when all of the following conditions are met:
- The invoice has been **submitted** (docstatus = 1)
- The invoice belongs to the selected **company** and **date range**
- The invoice has **non-zero taxes and charges** (i.e., VAT has been charged)
- The customer's address country is an **EU member state** (excluding Cyprus)

This breakdown helps you:
- Identify sales volume by EU member state
- Verify correct VAT rates are being applied
- Prepare for quarterly OSS VAT returns

## Filing Requirements

OSS VAT returns must be filed quarterly:

1. Generate the OSS VAT Returns report for the required period
2. Verify all figures against your sales records
3. Submit your OSS VAT return through the Cyprus OSS portal at [https://tax-oss.mof.gov.cy](https://tax-oss.mof.gov.cy)
4. Submit by the **end of the month** following the end of the quarter (e.g., Q1: Jan–Mar is due by 30 April)
5. Pay the total VAT amount by the same deadline
6. Maintain supporting documentation for at least 10 years

**Important Notes:**
- OSS applies only to B2C digital services, not physical goods or B2B services
- You must keep at least two pieces of evidence of each customer's location
- Different VAT rates apply in different EU countries — the app includes current rates for all member states
- Returns must be filed even if no eligible sales were made during the period (nil return)
- For more information, consult the [EU OSS guidelines](https://vat-one-stop-shop.ec.europa.eu/guides_en)

By following these guidelines, your OSS VAT Returns report will accurately reflect your digital service sales to EU consumers, facilitating compliance with EU VAT regulations.
