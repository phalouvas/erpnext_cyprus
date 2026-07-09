# Cyprus VAT Return Guide

The Cyprus VAT Return report in ERPNext Cyprus helps businesses prepare and submit their mandatory VAT returns to the Cyprus Tax Department. This guide explains how the report works, how to properly configure your system for accurate reporting, and how to interpret the results.

## Table of Contents
1. [Understanding the Cyprus VAT Return](#understanding-the-cyprus-vat-return)
2. [Company Configuration](#company-configuration)
3. [Tax Account Setup](#tax-account-setup)
4. [Transaction Configuration](#transaction-configuration)
5. [Report Structure](#report-structure)
6. [Report Interpretation](#report-interpretation)
7. [Filing Requirements](#filing-requirements)

## Understanding the Cyprus VAT Return

The Cyprus VAT Return (Form VAT 4) is a mandatory tax filing that all VAT-registered businesses in Cyprus must submit. The return:

- Reports VAT collected on sales and services (output tax)
- Reports VAT paid on purchases and expenses (input tax)
- Calculates net VAT payable or refundable
- Reports values of domestic sales, exports, and acquisitions
- Includes special categories for EU transactions and reverse charge scenarios

VAT returns in Cyprus must typically be filed quarterly, though monthly filings may be required for businesses with high turnover or specific profiles.

## Company Configuration

Before using the Cyprus VAT Return report:

1. Configure your company settings:
   - Ensure your company's Tax ID is properly set up with the CY prefix
   - Set up default currency as EUR
   - Configure your fiscal year to match Cyprus tax calendar

2. VAT registration details:
   - Enter your VAT registration number correctly
   - Set up VAT filing frequency (monthly or quarterly)
   - Configure tax calculation settings to match Cyprus requirements (19% standard rate, 9% reduced rate, 5% reduced rate, and 0% for zero-rated supplies)

## Tax Account Setup

The ERPNext Cyprus app automatically configures the necessary tax accounts and templates for accurate VAT reporting:

1. **Tax Accounts**:
   - **VAT Account**: Used for both input and output VAT transactions
   - **OSS VAT Account**: Specifically for Mini One Stop Shop reporting for B2C digital services to EU consumers

2. **Tax Templates**:
   - **Purchase Tax Templates**:
     - **Reverse Charge**: Double-entry template with 19% VAT for EU acquisitions (adds and deducts VAT in the same transaction)
     - **Standard Domestic**: For local purchases with 19% VAT
     - **Zero-Rated**: For exempt purchases or imports

   - **Sales Tax Templates**:
     - **Standard Domestic**: For local sales with 19% VAT
     - **Zero-Rated**: For EU B2B sales and exports
     - **Out-of-Scope**: For transactions outside the VAT system
     - **OSS Digital Services templates**: Country-specific templates for each EU member state with appropriate VAT rates

3. **Item Tax Templates**:
   - **Cyprus Standard 19%**: For standard-rated goods and services
   - **Cyprus Reduced 9%**: For reduced-rate items (e.g., restaurant services)
   - **Cyprus Super Reduced 5%**: For super reduced-rate items (e.g., books, medicines)
   - **Zero Rated**: For zero-rated supplies
   - **Exempt**: For exempt supplies

4. **Tax Rules**:
   The system automatically applies the correct tax template based on:
   - Customer/supplier country
   - Whether the transaction is B2B or B2C
   - Type of goods/services

5. **Service Items**:
   - Any product that is not a tangible product should be marked as "Is Service" in order
   
   These field determine how transactions are reported in boxes 8A/8B (supply of goods vs services) and 11A/11B (acquisition of goods vs services) of the VAT return.

## Transaction Configuration

For accurate VAT reporting, ensure your transactions are properly categorized:

1. Sales Invoices:
   - Apply the correct tax template based on the nature of the sale
   - For EU B2B sales, use zero-rated templates and include customer VAT numbers
   - For exports outside the EU, use zero-rated export templates
   - For local sales, use the appropriate VAT rate template

2. Purchase Invoices:
   - Apply the correct tax template based on the nature of the purchase
   - For EU acquisitions, use reverse charge templates
   - For local purchases, use standard VAT templates
   - For imports from outside the EU, correctly record import VAT

3. Item Configuration:
   - Mark items as goods or services using the "Is Service" field
   - This distinction is critical for EU reporting (Boxes 8A/8B and 11A/11B)

4. Customer/Supplier Configuration:
   - Properly record country and tax ID information
   - For EU businesses, ensure the tax ID includes the correct country prefix

## Report Structure

The Cyprus VAT Return report includes the following boxes:

1. **Box 1**: VAT due on sales and other outputs
   - Reports output VAT collected on domestic sales
   - Includes adjustments for credit notes

2. **Box 2**: VAT due on acquisitions from EU countries
   - Reports VAT due under reverse charge for EU acquisitions
   - Represents the output portion of the reverse charge mechanism
   - **Three-tier calculation**:
     1. *Primary*: Reverse-charge output VAT from Purchase Invoice tax rows (Deduct type on Output VAT account) for EU supplier invoices
     2. *Fallback*: If no PI tax rows exist and EU acquisitions are present (Box 11A + Box 11B > 0), computes VAT as `fallback_rate × (Box 11A + Box 11B)`
     3. *Adjustment*: Adds marked Journal Entry adjustments (net credits with `VAT-RC-ADJ` marker) on the Output VAT account

3. **Box 3**: Total VAT due (sum of boxes 1 and 2)
   - Total output VAT liability for the period

4. **Box 4**: VAT reclaimed on purchases and other inputs
   - Reports input VAT paid on domestic purchases and expenses
   - Includes VAT reclaimed on imports and EU acquisitions
   - Includes adjustments for debit notes
   - **Five-component calculation**:
     1. *Sales GL*: Input VAT from Sales Invoice credit notes (via GL entries on Input VAT account)
     2. *Purchase GL*: Input VAT from domestic Purchase Invoices with GL postings
     3. *PI Tax Rows*: Reverse-charge input VAT from EU acquisition Purchase Invoice tax rows (Add type on Input VAT account)
     4. *Fallback mirror*: If PI tax rows are empty and EU acquisitions exist, adds mirror fallback amount
     5. *JE Adjustment*: Adds marked Journal Entry adjustments (net debits with `VAT-RC-ADJ` marker) on the Input VAT account

5. **Box 5**: Net VAT to be paid or reclaimed
   - The difference between Box 3 and Box 4
   - Represents final VAT payable (if positive) or refundable (if negative)

6. **Box 6**: Total value of sales and other outputs excluding VAT
   - Reports net value of all sales and outputs (excluding VAT)
   - Includes domestic sales, EU supplies, exports, and out-of-scope sales

7. **Box 7**: Total value of purchases and inputs excluding VAT
   - Reports net value of all purchases and inputs (excluding VAT)
   - Includes domestic purchases, EU acquisitions, and imports

8. **Box 8A**: Total value of supplies of goods to EU countries
   - Reports value of goods supplied to VAT-registered businesses in other EU countries
   - Must be reported separately for EU Intrastat reporting

9. **Box 8B**: Total value of supplies of services to EU countries
   - Reports value of services supplied to VAT-registered businesses in other EU countries
   - Subject to place of supply rules

10. **Box 9**: Total value of exports to non-EU countries
    - Reports value of goods exported to countries outside the EU
    - Zero-rated for VAT purposes

11. **Box 10**: Total value of out-of-scope sales
    - Reports value of sales that are outside the scope of VAT but with right to input tax deduction

12. **Box 11A**: Total value of acquisitions of goods from EU countries
    - Reports value of goods acquired from VAT-registered businesses in other EU countries
    - Subject to reverse charge mechanism

13. **Box 11B**: Total value of acquisitions of services from EU countries
    - Reports value of services acquired from VAT-registered businesses in other EU countries
    - Subject to reverse charge mechanism and place of supply rules

## Report Interpretation

The Cyprus VAT Return report provides:

- **Field**: Box number as referenced in the official VAT return form
- **Description**: Explanation of what the box represents
- **Amount (EUR)**: The calculated value for the reporting period

Key points to understand:

1. **VAT Payment/Refund**: Box 5 shows whether you need to pay VAT (positive number) or are entitled to a refund (negative number)

2. **EU Reporting**: Boxes 8A, 8B, 11A, and 11B help identify transactions that may need to be included in VIES statements

3. **Cross-Validation**: You should verify that:
   - Box 6 includes the values from Boxes 8A, 8B, 9, 10, and the domestic supplies
   - Box 7 includes the values from Boxes 11A and 11B, plus domestic purchases
   - Box 2 represents the output VAT equivalent for the values in Boxes 11A and 11B
   
4. **Common Issues**:
   - Mismatch between VAT return and your VIES statements
   - Missing reverse charge entries for EU acquisitions
   - Incorrect tax templates applied to transactions
   - EU suppliers without `supplier_address` set — these transactions are excluded from Box 11A/11B

## Calculation Details

### Reverse-Charge VAT (Box 2 and Box 4 components)

For EU acquisitions using Reverse Charge tax templates, the report uses a three-tier calculation:

1. **PI Tax Rows (Primary)**: Reads directly from the `Purchase Taxes and Charges` child table for each Purchase Invoice where the supplier is in an EU country. Deduct rows on the Output VAT account contribute to Box 2; Add rows on the Input VAT account contribute to Box 4.

2. **Fallback**: When Purchase Invoices use a Reverse Charge template but have no actual tax rows applied (`taxes: []`), the report computes the reverse-charge VAT as:
   ```
   fallback_rate × (Box 11A + Box 11B)
   ```
   The fallback rate is derived from the company's Purchase Taxes and Charges Template (Reverse Charge) if available, defaulting to 19% (Cyprus standard rate).

3. **JE Adjustments**: Journal Entries with the marker prefix `VAT-RC-ADJ` in the Remark field are included as adjustment layer. The report filters by:
   - `voucher_type = 'Journal Entry'`
   - `docstatus = 1` (submitted)
   - `account` = selected Output or Input VAT account
   - `remark LIKE 'VAT-RC-ADJ:%'`

### JE Marker Policy

To include manual corrections in the VAT return:
- Create a Journal Entry with lines on the appropriate VAT accounts
- Add the marker prefix `VAT-RC-ADJ:` in the Journal Entry **Remark** field
- Example: `VAT-RC-ADJ: Correction for Q1 2026`
- Journal Entries without this marker are **excluded** from adjustment totals

### Diagnostics and Pre-Filing Checks

The report shows diagnostic warnings at the bottom when potential data quality issues are detected:

| Diagnostic | Severity | Description |
|------------|----------|-------------|
| Empty PI tax rows | Warning | PI uses Reverse Charge template but tax rows are empty → fallback used |
| Missing supplier address | Warning | EU supplier PI without `supplier_address` → excluded from Box 11A/11B |
| Box 2 = 0 with EU acquisitions | Warning | Box 11A+11B > 0 but Box 2 is zero → check templates and master data |
| Unmarked JE candidates | Warning | JE on VAT accounts without `VAT-RC-ADJ` marker → excluded from totals |

### Fallback Deprecation

The fallback (tier 2) using `rate × (Box 11A + Box 11B)` is a **transitional mechanism** to handle cases where Reverse Charge tax templates are selected on Purchase Invoices but tax rows are not applied. It should be phased out once all EU acquisition Purchase Invoices consistently have populated tax rows.

## Filing Requirements

Filing requirements for Cyprus VAT returns:

1. **Submission Frequency**:
   - Quarterly for most businesses
   - Monthly for businesses with annual turnover exceeding €1,500,000

2. **Filing Deadlines**:
   - Within 40 days from the end of the VAT period
   - Payment must be made by the same deadline

3. **Filing Methods**:
   - Electronic filing through the TAXISnet system
   - Paper submission is no longer accepted for most businesses

4. **Documentation**:
   - Keep all supporting documentation for at least 6 years
   - This includes invoices, credit notes, import documents, etc.

5. **Penalties**:
   - Late filing penalties: €51 per return
   - Late payment penalties: 10% of unpaid tax
   - Interest on late payments: Currently 1.75% per annum

6. **VAT Adjustments**:
   - If you discover errors in previous returns, corrections should be made
   - Minor errors can be adjusted in the current return
   - Major errors require submission of revised returns

By following these guidelines and properly configuring your ERPNext Cyprus system, your Cyprus VAT Return report will accurately reflect your VAT obligations, helping you maintain compliance with Cyprus tax regulations and avoid potential penalties.