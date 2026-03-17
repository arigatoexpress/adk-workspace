"""
Inventory Tools for Texas Home Outlet Sales Agent.

These tools enable the Sales Agent to search inventory and calculate financing.
"""

from google.adk.tools import ToolContext
from typing import Optional
from datetime import datetime


# Sample inventory data - In production, this would query Firestore
SAMPLE_INVENTORY = [
    {
        "id": "THO-2024-001",
        "manufacturer": "Jessup Housing",
        "model_name": "The Nassau",
        "classification": "Double Wide",
        "status": "Available",
        "specs": {"beds": 3, "baths": 2, "sq_ft": 1264},
        "pricing": {"price_value": 89900, "display_price": "$89,900", "price_tier": "$75k-$100k"},
        "features": ["Island Kitchen", "Walk-in Closet", "Garden Tub"],
        "marketing_tags": ["Featured", "Best Seller"]
    },
    {
        "id": "THO-2024-002",
        "manufacturer": "TRU",
        "model_name": "The Delight",
        "classification": "Single Wide",
        "status": "Clearance",
        "specs": {"beds": 3, "baths": 2, "sq_ft": 1056},
        "pricing": {"price_value": 62500, "display_price": "$62,500", "price_tier": "$50k-$75k"},
        "features": ["Energy Star", "Open Floor Plan"],
        "marketing_tags": ["Red Tag", "Year End Clearance"]
    },
    {
        "id": "THO-2024-003",
        "manufacturer": "Clayton",
        "model_name": "The Elite",
        "classification": "Double Wide",
        "status": "Available",
        "specs": {"beds": 4, "baths": 2, "sq_ft": 1680},
        "pricing": {"price_value": 124900, "display_price": "$124,900", "price_tier": "$100k-$150k"},
        "features": ["Master Suite", "Dual Vanity", "Entertainment Center", "Island Kitchen"],
        "marketing_tags": ["New Arrival"]
    },
    {
        "id": "THO-2024-004",
        "manufacturer": "Champion",
        "model_name": "The Maverick",
        "classification": "Single Wide",
        "status": "Available",
        "specs": {"beds": 2, "baths": 1, "sq_ft": 784},
        "pricing": {"price_value": 45900, "display_price": "$45,900", "price_tier": "Under $50k"},
        "features": ["Compact Design", "Energy Efficient"],
        "marketing_tags": ["Budget Friendly"]
    }
]


def search_inventory(
    min_beds: Optional[int] = None,
    max_beds: Optional[int] = None,
    min_baths: Optional[float] = None,
    max_budget: Optional[float] = None,
    classification: Optional[str] = None,
    status: Optional[str] = None,
    features: Optional[list[str]] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Search THO inventory based on customer preferences.
    
    Args:
        min_beds: Minimum number of bedrooms
        max_beds: Maximum number of bedrooms  
        min_baths: Minimum number of bathrooms
        max_budget: Maximum price budget
        classification: Home type (Single Wide, Double Wide, Modular)
        status: Availability status (Available, Clearance, Red Tag)
        features: Required features list
        tool_context: ADK tool context
    
    Returns:
        Dictionary with matching homes and search summary
    """
    results = []
    
    for home in SAMPLE_INVENTORY:
        # Apply filters
        if min_beds and home["specs"]["beds"] < min_beds:
            continue
        if max_beds and home["specs"]["beds"] > max_beds:
            continue
        if min_baths and home["specs"]["baths"] < min_baths:
            continue
        if max_budget and home["pricing"]["price_value"] > max_budget:
            continue
        if classification and home["classification"].lower() != classification.lower():
            continue
        if status and home["status"].lower() != status.lower():
            continue
        if features:
            home_features = [f.lower() for f in home["features"]]
            if not all(f.lower() in home_features for f in features):
                continue
        
        results.append(home)
    
    # Sort by price
    results.sort(key=lambda x: x["pricing"]["price_value"])
    
    return {
        "success": True,
        "count": len(results),
        "homes": results,
        "search_summary": f"Found {len(results)} homes matching your criteria.",
        "tip": "Ask about financing options or schedule a showing!" if results else "Try broadening your search criteria."
    }


def calculate_payment(
    price: float,
    down_payment: float = 0,
    term_months: int = 240,
    interest_rate: float = 8.5,
    tool_context: ToolContext = None
) -> dict:
    """
    Calculate estimated monthly payment for financing.
    
    Uses standard amortization formula. This is an ESTIMATE only - 
    actual rates depend on credit qualification through 21st Mortgage.
    
    Args:
        price: Home price in dollars
        down_payment: Down payment amount in dollars
        term_months: Loan term in months (default 240 = 20 years)
        interest_rate: Annual interest rate percentage (default 8.5%)
        tool_context: ADK tool context
    
    Returns:
        Dictionary with payment breakdown
    """
    loan_amount = price - down_payment
    
    if loan_amount <= 0:
        return {
            "success": True,
            "message": "With that down payment, you'd own the home outright! No financing needed.",
            "monthly_payment": 0
        }
    
    # Monthly interest rate
    monthly_rate = interest_rate / 100 / 12
    
    # Amortization formula: M = P * [r(1+r)^n] / [(1+r)^n - 1]
    if monthly_rate > 0:
        payment = loan_amount * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
    else:
        payment = loan_amount / term_months
    
    return {
        "success": True,
        "home_price": f"${price:,.2f}",
        "down_payment": f"${down_payment:,.2f}",
        "loan_amount": f"${loan_amount:,.2f}",
        "term_years": term_months // 12,
        "interest_rate": f"{interest_rate}%",
        "monthly_payment": f"${payment:,.2f}",
        "monthly_payment_value": round(payment, 2),
        "disclaimer": "This is an ESTIMATE only. Actual rates and terms depend on credit qualification through 21st Mortgage or other lenders. Contact us for a personalized quote!"
    }
