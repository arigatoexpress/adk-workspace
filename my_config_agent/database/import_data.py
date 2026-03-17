"""
Data Import Tool - Import spreadsheet data to Firestore
Processes Tenant Roster, House Orders, and Property Taxes spreadsheets
"""

import re
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path

# Import models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from database.models import Customer, Property, Inventory, Lease, TaxPayment, CustomerStatus


def parse_phone_email(name_field: str) -> Tuple[str, Optional[str], Optional[str]]:
    """Parse name field that contains 'Name - (phone) - email' format"""
    # Example: "Guadalupe Andrade - (832) 366-4694 - "
    if pd.isna(name_field):
        return "", None, None
    
    parts = str(name_field).split(" - ")
    name = parts[0].strip() if parts else ""
    phone = None
    email = None
    
    for part in parts[1:]:
        part = part.strip()
        # Check if phone
        if part.startswith("(") or re.match(r'\d{3}', part):
            phone = part
        # Check if email
        elif "@" in part:
            email = part
    
    return name, phone, email


def parse_model_specs(model_name: str) -> Dict:
    """Parse home specs from model name like 'Elation Smart 14x66' or 'Creole 32x60 3/2'"""
    specs = {
        "bedrooms": None,
        "bathrooms": None,
        "width": None,
        "length": None,
        "sqft": None
    }
    
    if pd.isna(model_name):
        return specs
    
    model = str(model_name)
    
    # Parse dimensions like 14x66, 28x60, 32x60
    dim_match = re.search(r'(\d{2})x(\d{2})', model)
    if dim_match:
        specs["width"] = int(dim_match.group(1))
        specs["length"] = int(dim_match.group(2))
        specs["sqft"] = specs["width"] * specs["length"]
    
    # Parse bed/bath like 3/2, 4/2
    bb_match = re.search(r'(\d)/(\d)', model)
    if bb_match:
        specs["bedrooms"] = int(bb_match.group(1))
        specs["bathrooms"] = int(bb_match.group(2))
    
    return specs


def clean_currency(value) -> Optional[float]:
    """Convert currency string to float"""
    if pd.isna(value):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    
    # Remove $, commas, spaces
    cleaned = re.sub(r'[$,\s]', '', str(value))
    try:
        return float(cleaned)
    except:
        return None


def import_tenant_roster(csv_path: str) -> List[Dict]:
    """
    Import Tenant Roster CSV
    Returns list of customer + lease records
    """
    df = pd.read_csv(csv_path, skiprows=1)  # Skip title row
    
    records = []
    current_account = None
    
    for _, row in df.iterrows():
        account = row.get("Account Name", "")
        name_field = row.get("Name", "")
        address = row.get("Address", "")
        amount = row.get(" Amount ", row.get("Amount", ""))
        lease_end = row.get("Lease-End", "")
        status = row.get("Status", "")
        
        # Skip subtotal rows and empty rows
        if pd.isna(name_field) or "Subtotal" in str(account):
            if not pd.isna(account) and "Subtotal" not in str(account):
                current_account = account
            continue
        
        # Parse name field
        name, phone, email = parse_phone_email(name_field)
        if not name:
            continue
        
        # Determine status
        cust_status = CustomerStatus.ENROLLED if status == "ENROLLED" else CustomerStatus.NON_ENROLLED
        
        # Parse amount
        monthly_payment = clean_currency(amount)
        
        # Parse lease end date
        lease_end_date = None
        if not pd.isna(lease_end) and lease_end != "N/A":
            try:
                lease_end_date = pd.to_datetime(lease_end).date()
            except:
                pass
        
        record = {
            "customer": {
                "full_name": name,
                "phone": phone,
                "email": email,
                "status": cust_status.value,
                "billing_account": current_account or account
            },
            "property": {
                "address": address
            },
            "lease": {
                "monthly_payment": monthly_payment,
                "lease_end_date": str(lease_end_date) if lease_end_date else None,
                "billing_account": current_account or account,
                "status": "active" if status == "ENROLLED" else "inactive"
            }
        }
        records.append(record)
    
    return records


def import_house_orders(xlsx_path: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Import House Orders XLSX
    Returns (available_inventory, sold_inventory)
    """
    # Read both sheets
    active_df = pd.read_excel(xlsx_path, sheet_name="Everybody Else", header=1)
    sold_df = pd.read_excel(xlsx_path, sheet_name="Sold Stuff", header=1)
    
    def process_sheet(df, is_sold=False):
        records = []
        
        # Map columns (they have Unnamed due to merged cells)
        col_map = {
            "Serial #": "serial_number",
            "Manufacturing Plant": "manufacturer",
            "Model": "model_name",
            "Invoice Date": "invoice_date",
            "Invoice Amount": "invoice_amount",
            "MSRP": "msrp",
            "Customer": "customer_name",
            "Salesman": "salesman",
            "Customer #": "customer_number"
        }
        
        for _, row in df.iterrows():
            serial = row.get("Serial #")
            if pd.isna(serial):
                continue
            
            model_name = row.get("Model", "")
            specs = parse_model_specs(model_name)
            
            record = {
                "serial_number": str(serial),
                "manufacturer": row.get("Manufacturing Plant"),
                "model_name": model_name,
                "invoice_date": str(row.get("Invoice Date").date()) if not pd.isna(row.get("Invoice Date")) else None,
                "invoice_amount": clean_currency(row.get("Invoice Amount")),
                "msrp": clean_currency(row.get("MSRP")),
                "status": "SOLD" if is_sold else "AVAILABLE",
                "bedrooms": specs["bedrooms"],
                "bathrooms": specs["bathrooms"],
                "width": specs["width"],
                "length": specs["length"],
                "sqft": specs["sqft"],
                # Customer info for sold items
                "customer_name": row.get("Customer") if not pd.isna(row.get("Customer")) else None,
                "salesman": row.get("Salesman") if not pd.isna(row.get("Salesman")) else None,
                "customer_number": row.get("Customer #") if not pd.isna(row.get("Customer #")) else None
            }
            records.append(record)
        
        return records
    
    available = process_sheet(active_df, is_sold=False)
    sold = process_sheet(sold_df, is_sold=True)
    
    return available, sold


def import_property_taxes(xlsx_path: str) -> List[Dict]:
    """
    Import Property Taxes XLSX
    Returns list of property + tax payment records
    """
    # Read specific tax year sheets
    tax_years = ["2021 Tax Payments", "2022 Tax Payments", "2023 Tax Payments", 
                 "2024 Tax Payments", "2025 Tax Payments"]
    
    records = []
    
    for sheet_name in tax_years:
        try:
            df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=1)
        except:
            continue
        
        year = int(sheet_name.split()[0])
        
        for _, row in df.iterrows():
            customer = row.get("Customer")
            if pd.isna(customer):
                continue
            
            address = row.get("Address")
            if pd.isna(address):
                continue
            
            record = {
                "customer_name": customer,
                "property": {
                    "address": address,
                    "county": row.get("County"),
                    "school_district": row.get("School District"),
                    "county_account_number": row.get("Acct number"),
                    "county_tax_link": row.get("County Web Link"),
                    "isd_tax_link": row.get("ISD Web Link")
                },
                "tax_payment": {
                    "tax_year": year,
                    "county_taxes": clean_currency(row.get("County Taxes")),
                    "school_taxes": clean_currency(row.get("School District Taxes")),
                    "total_taxes": clean_currency(row.get("Total Taxes")),
                    "escrow_balance": clean_currency(row.get("Escrow Balance as of 12/31/xx"))
                }
            }
            records.append(record)
    
    return records


def run_full_import(
    tenant_roster_path: str,
    house_orders_path: str,
    property_taxes_path: str
) -> Dict:
    """Run full data import and return summary"""
    summary = {
        "tenants": 0,
        "properties": 0,
        "inventory_available": 0,
        "inventory_sold": 0,
        "tax_records": 0
    }
    
    # Import tenant roster
    if tenant_roster_path:
        tenants = import_tenant_roster(tenant_roster_path)
        summary["tenants"] = len(tenants)
        print(f"Imported {len(tenants)} tenant records")
    
    # Import house orders
    if house_orders_path:
        available, sold = import_house_orders(house_orders_path)
        summary["inventory_available"] = len(available)
        summary["inventory_sold"] = len(sold)
        print(f"Imported {len(available)} available homes, {len(sold)} sold homes")
    
    # Import property taxes
    if property_taxes_path:
        taxes = import_property_taxes(property_taxes_path)
        summary["tax_records"] = len(taxes)
        summary["properties"] = len(set(r["property"]["address"] for r in taxes))
        print(f"Imported {len(taxes)} tax records for {summary['properties']} properties")
    
    return summary


if __name__ == "__main__":
    # Default paths
    base_path = "/Users/aribs/Documents/Google Sheets"
    
    summary = run_full_import(
        tenant_roster_path=f"{base_path}/RosterInfoForTenantRosterasofFebruary52026.csv",
        house_orders_path=f"{base_path}/House Orders.xlsx",
        property_taxes_path=f"{base_path}/THO Combined Portfolio - Property Taxes.xlsx"
    )
    
    print("\n=== IMPORT SUMMARY ===")
    for key, value in summary.items():
        print(f"  {key}: {value}")
