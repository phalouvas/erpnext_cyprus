"""
Shared test fixture builders for erpnext_cyprus.

Each function creates and returns a record (or record name). All records are
persisted to the database so tests can freely query them. Each test module is
responsible for cleaning up its own records in tearDown.

Builders are designed to be idempotent: if a record with the same name already
exists they return the existing name; if not they create one. This allows
multiple test modules to coexist without conflicts as long as they use unique
names or share the same setUp/tearDown lifecycle.
"""

import frappe
from frappe.utils import today

# ── Territories ──────────────────────────────────────────────────────────

REQUIRED_TERRITORIES = ["All Territories", "EU", "Cyprus", "Rest Of The World"]


def ensure_territories():
    """Pre-create territories expected by the customer_group_assignment hook."""
    for name in REQUIRED_TERRITORIES:
        if not frappe.db.exists("Territory", name):
            frappe.get_doc({"doctype": "Territory", "territory_name": name}).insert()


# ── Company ──────────────────────────────────────────────────────────────

def build_company(company_name, abbr, country="Cyprus", currency="EUR"):
    """Create a test company with minimum required defaults."""
    if frappe.db.exists("Company", company_name):
        return company_name

    ensure_territories()

    company = frappe.get_doc({
        "doctype": "Company",
        "company_name": company_name,
        "abbr": abbr,
        "country": country,
        "default_currency": currency,
    })
    company.insert()

    # Remove auto-created Tax Rules for the test company so they don't
    # interfere with Sales Invoice creation during tests
    frappe.db.delete("Tax Rule", {"company": company_name})

    # Ensure a selling price list exists (required by Sales Invoice validation)
    if not frappe.db.exists("Price List", f"Test Selling - {abbr}"):
        build_price_list(company_name, abbr, f"Test Selling - {abbr}", selling=True)

    # Create round-off cost centre
    _create_cost_center(company_name, abbr, "Main")
    # Create round-off account
    _create_account_by_abbr(company_name, abbr, "Round Off", "Expense")

    cc_name = f"Main - {abbr}"
    ro_acct = f"Round Off - {abbr}"
    company.db_set("round_off_cost_center", cc_name)
    company.db_set("round_off_account", ro_acct)

    return company_name


def get_company_abbr(company_name):
    """Fetch a company's abbreviation."""
    return frappe.db.get_value("Company", company_name, "abbr")


# ── Account ──────────────────────────────────────────────────────────────

def build_account(company_name, abbr, account_name, root_type, account_type=None):
    """Get or create an account under the correct parent."""
    name = f"{account_name} - {abbr}"
    if frappe.db.exists("Account", name):
        return name

    parent = frappe.db.get_value("Account", {
        "company": company_name,
        "root_type": root_type,
        "is_group": 1,
    }, "name")

    doc = frappe.get_doc({
        "doctype": "Account",
        "account_name": account_name,
        "company": company_name,
        "root_type": root_type,
        "account_type": account_type,
        "parent_account": parent,
        "is_group": 0,
    })
    doc.insert()
    return doc.name


# ── Cost Centre ──────────────────────────────────────────────────────────

def build_cost_center(company_name, abbr, name):
    """Get or create a cost centre."""
    full = f"{name} - {abbr}"
    if frappe.db.exists("Cost Center", full):
        return full

    return _create_cost_center(company_name, abbr, name)


# ── Warehouse ────────────────────────────────────────────────────────────

def build_warehouse(company_name, abbr, name="Stores"):
    """Get or create a warehouse."""
    full = f"{name} - {abbr}"
    if frappe.db.exists("Warehouse", full):
        return full

    doc = frappe.get_doc({
        "doctype": "Warehouse",
        "warehouse_name": name,
        "company": company_name,
        "is_group": 0,
    })
    doc.insert()
    return doc.name


# ── Item ─────────────────────────────────────────────────────────────────

def build_item(item_code, item_name=None, is_service=1, is_stock_item=0):
    """Get or create an item."""
    if frappe.db.exists("Item", item_code):
        return item_code

    doc = frappe.get_doc({
        "doctype": "Item",
        "item_code": item_code,
        "item_name": item_name or item_code,
        "item_group": "Services",
        "is_service": is_service,
        "is_stock_item": is_stock_item,
    })
    doc.insert()
    return doc.name


# ── Customer with optional Address ──────────────────────────────────────

def build_customer(customer_name, country, tax_id="", has_address=True):
    """Get or create a customer with optional address."""
    if frappe.db.exists("Customer", customer_name):
        return customer_name

    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_type": "Company",
        "tax_id": tax_id,
    })
    customer.insert()

    if has_address and country:
        build_address(f"{customer_name}-Addr", country, customer_name)

    return customer.name


# ── Address ──────────────────────────────────────────────────────────────

def build_address(address_title, country, link_name):
    """Get or create an address linked to a customer."""
    if frappe.db.exists("Address", {"address_title": address_title}):
        addr_name = frappe.db.get_value("Address", {"address_title": address_title}, "name")
        return addr_name

    address = frappe.get_doc({
        "doctype": "Address",
        "address_title": address_title,
        "address_type": "Billing",
        "address_line1": "123 Test Street",
        "city": "Test City",
        "country": country,
        "links": [{"link_doctype": "Customer", "link_name": link_name}],
    })
    address.insert()

    # Set as primary address for the customer
    frappe.db.set_value("Customer", link_name, "customer_primary_address", address.name)

    return address.name


# ── Price List ──────────────────────────────────────────────────────────

def build_price_list(company_name, abbr, name, selling=False, buying=False, currency="EUR"):
    """Get or create a price list."""
    if frappe.db.exists("Price List", name):
        return name
    pl = frappe.get_doc({
        "doctype": "Price List",
        "price_list_name": name,
        "enabled": 1,
        "selling": 1 if selling else 0,
        "buying": 1 if buying else 0,
        "currency": currency,
    })
    pl.insert()
    return pl.name


# ── Sales Invoice ────────────────────────────────────────────────────────

def build_sales_invoice(
    company,
    customer,
    net_total,
    posting_date=None,
    is_return=False,
    return_against=None,
    do_not_submit=False,
    customer_address=None,
    item_code="_Test Cyprus Item",
    warehouse=None,
    income_account=None,
    debtor_account=None,
    cost_center=None,
):
    """Create a Sales Invoice for testing.

    Parameters
    ----------
    company : str
    customer : str
    net_total : float   — item rate (qty=1)
    posting_date : str, optional
    is_return : bool, optional
    return_against : str, optional
    do_not_submit : bool — if True the doc is inserted but not submitted
    customer_address : str, optional
    """
    if posting_date is None:
        posting_date = today()

    abbr = get_company_abbr(company)

    income = income_account or build_account(company, abbr, "Sales", "Income")
    debtor = debtor_account or build_account(company, abbr, "Debtors", "Receivable", account_type="Receivable")
    cc = cost_center or build_cost_center(company, abbr, "Main")
    wh = warehouse or build_warehouse(company, abbr)
    item = item_code
    if not frappe.db.exists("Item", item):
        item = build_item(item_code)
    price_list = f"Test Selling - {abbr}"

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "company": company,
        "customer": customer,
        "posting_date": posting_date,
        "due_date": posting_date,
        "currency": "EUR",
        "debit_to": debtor,
        "is_return": is_return,
        "return_against": return_against,
        "customer_address": customer_address,
        "selling_price_list": price_list,
        "price_list_currency": "EUR",
        "plc_conversion_rate": 1.0,
        "items": [
            {
                "item_code": item,
                "qty": 1,
                "rate": net_total,
                "income_account": income,
                "cost_center": cc,
                "warehouse": wh,
            }
        ],
    })
    si.insert()

    if not do_not_submit:
        si.submit()

    si.load_from_db()
    return si.name

    if not do_not_submit:
        si.submit()

    si.load_from_db()
    return si.name


# ── Internal helpers ─────────────────────────────────────────────────────

def _create_cost_center(company_name, abbr, name):
    """Create a single cost centre if it does not already exist."""
    full = f"{name} - {abbr}"
    if frappe.db.exists("Cost Center", full):
        return full
    parent = frappe.db.get_value("Cost Center", {
        "company": company_name,
        "is_group": 1,
    }, "name")
    doc = frappe.get_doc({
        "doctype": "Cost Center",
        "cost_center_name": name,
        "company": company_name,
        "parent_cost_center": parent,
        "is_group": 0,
    })
    doc.insert()
    return full


def _create_account_by_abbr(company_name, abbr, account_name, root_type, account_type=None):
    """Create a single account if it does not already exist."""
    full = f"{account_name} - {abbr}"
    if frappe.db.exists("Account", full):
        return full
    parent = frappe.db.get_value("Account", {
        "company": company_name,
        "root_type": root_type,
        "is_group": 1,
    }, "name")
    doc = frappe.get_doc({
        "doctype": "Account",
        "account_name": account_name,
        "company": company_name,
        "root_type": root_type,
        "account_type": account_type,
        "parent_account": parent,
        "is_group": 0,
    })
    doc.insert()
    return full
