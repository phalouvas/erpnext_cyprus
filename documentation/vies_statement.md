# VIES Statement Guide for Cyprus

The VIES (VAT Information Exchange System) Statement in ERPNext Cyprus helps businesses report intra-Community supplies of goods and services to other EU member states. This guide explains how to properly set up and mark transactions for accurate VIES reporting.

## Table of Contents
1. [Understanding VIES](#understanding-vies)
2. [Company Configuration](#company-configuration)
3. [Customer Configuration](#customer-configuration)
4. [Sales Transactions](#sales-transactions)
5. [Report Interpretation](#report-interpretation)
6. [Filing Requirements](#filing-requirements)

## Understanding VIES

VIES is an EU VAT system that:
- Validates VAT numbers of EU businesses
- Enables exchange of information about intra-EU supplies
- Requires businesses to submit periodic VIES statements for B2B transactions
- Helps tax authorities ensure VAT compliance for cross-border transactions

In Cyprus, businesses must report sales of goods and services to VAT-registered businesses in other EU member states through a VIES statement.

## Company Configuration

Before using VIES reporting:

1. Configure your company settings:
   - Ensure your company's Tax ID is properly set up with the CY prefix
   - Register for VAT VIES reporting with Cyprus tax authorities
   - Set up appropriate numbering series for sales invoices

2. Tax configuration:
   - Create zero-rated tax templates for EU B2B sales
   - Ensure these templates are labeled appropriately for easy identification

## Customer Configuration

Proper customer setup is crucial for VIES reporting:

1. For B2B customers in other EU member states:
   - Create customer records with correct country field set
   - Enter their valid VAT registration number in the Tax ID field
   - The Tax ID must include the proper country prefix (e.g., DE12345678 for Germany)

2. Validate EU VAT numbers:
   - Use the EU VAT number validation service (VIES website)
   - Store validation proof with customer records
   - Regularly check for validity as invalid VAT numbers can lead to compliance issues

3. Customer grouping:
   - Consider creating a specific customer group for "EU B2B Customers" for easier filtering
   - Tag customers appropriately to streamline VIES reporting

## Sales Transactions

When creating sales invoices for EU B2B customers:

1. Select the correct customer with valid EU VAT number
2. Apply zero-rated VAT (reverse charge):
   - Select the appropriate EU B2B zero-rated tax template
   - Verify no VAT is being charged
   - Include the note "VAT Reverse Charge" on the invoice

3. For each transaction, ensure:
   - Invoice is submitted (docstatus = 1) to appear in the VIES report
   - Customer's Tax ID is correctly entered
   - Invoice includes all required information for EU cross-border compliance
   - Amount is correctly calculated and rounded as needed

4. Important invoice notations:
   - Include a reference to the reverse charge mechanism
   - Mention the legal basis (EU VAT Directive Article 44)
   - Include both your VAT number and the customer's VAT number

## Report Interpretation

The VIES Statement report provides customer-aggregated totals:

- **Customer**: The name of the EU business customer
- **Country**: The customer's country (derived from the `customer_address` field on the invoice)
- **Tax ID**: The customer's VAT registration number
- **Net Total**: Sum of net values of all invoices for this customer in the selected period
- **Rounded Net Total**: Sum of individually rounded net values

### Inclusion Criteria

The report includes a Sales Invoice row when all of the following conditions are met:
- The invoice has been **submitted** (docstatus = 1)
- The invoice belongs to the selected **company** and **date range**
- The invoice has **zero total taxes and charges** (zero-rated for VIES purposes)
- The customer has a **Tax ID** entered (non-empty)
- The invoice has a **customer address** set with a country in the **EU** (excluding Cyprus)

This output helps you:
- Prepare for VIES recapitulative statement submission
- Verify all EU B2B sales have been properly recorded
- Ensure all transactions have valid Tax IDs
- Review aggregated totals per customer for monthly or quarterly periods

## Filing Requirements

VIES statements in Cyprus:

1. Submission frequency:
   - Monthly if the value of goods exceeds thresholds set by tax authorities
   - Quarterly for services or when below thresholds

2. Submission process:
   - Generate the VIES Statement report for the required period
   - Verify all entries against your sales records
   - Submit the statement through the Cyprus TAXISnet portal
   - Submit by the 15th day of the month following the reporting period

3. Record keeping:
   - Maintain copies of all submitted VIES statements
   - Keep supporting documentation for at least 7 years
   - Include proof of customer VAT number validation
   - Store copies of invoices with proper reverse charge notations

**Important Notes:**
- VIES reporting applies only to B2B transactions with VAT-registered businesses in other EU member states
- Zero-rating is only valid when the customer provides a valid EU VAT number
- Failure to report or incorrect reporting can result in penalties
- All amounts should be reported in Euro

By following these guidelines, your VIES Statement report will accurately reflect your intra-Community supplies, facilitating compliance with EU VAT regulations and helping prevent potential issues during tax audits.
