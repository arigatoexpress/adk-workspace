"""
CRM Tools for Texas Home Outlet Sales Agent.

These tools enable the Sales Agent to book appointments and manage leads.
"""

from google.adk.tools import ToolContext
from typing import Optional
from datetime import datetime, timedelta
import uuid


# Available time slots (simplified - in production this would check a calendar)
BUSINESS_HOURS = {
    "Monday": ("9:00 AM", "6:00 PM"),
    "Tuesday": ("9:00 AM", "6:00 PM"),
    "Wednesday": ("9:00 AM", "6:00 PM"),
    "Thursday": ("9:00 AM", "6:00 PM"),
    "Friday": ("9:00 AM", "6:00 PM"),
    "Saturday": ("9:00 AM", "5:00 PM"),
    "Sunday": ("12:00 PM", "3:00 PM")
}

LOCATION = {
    "name": "Texas Home Outlet",
    "address": "2915 FM 1960 E, Huffman, TX 77336",
    "phone": "(281) 324-1111"
}


def book_appointment(
    customer_name: str,
    customer_phone: str,
    customer_email: Optional[str] = None,
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
    notes: Optional[str] = None,
    has_land: Optional[bool] = None,
    interested_in: Optional[str] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Book a showroom visit or consultation appointment.
    
    Args:
        customer_name: Customer's full name
        customer_phone: Customer's phone number
        customer_email: Customer's email (optional)
        preferred_date: Preferred date (YYYY-MM-DD format)
        preferred_time: Preferred time (e.g., "10:00 AM", "2:00 PM")
        notes: Additional notes about what the customer is looking for
        has_land: Whether the customer already owns land
        interested_in: Specific home model or type they're interested in
        tool_context: ADK tool context
    
    Returns:
        Dictionary with appointment confirmation
    """
    appointment_id = f"APT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    
    # Parse or suggest date
    if preferred_date:
        try:
            appt_date = datetime.strptime(preferred_date, "%Y-%m-%d")
            day_name = appt_date.strftime("%A")
        except ValueError:
            return {
                "success": False,
                "error": "Invalid date format. Please use YYYY-MM-DD format."
            }
    else:
        # Suggest next available day (skip to next business day)
        appt_date = datetime.now() + timedelta(days=1)
        while appt_date.strftime("%A") == "Sunday":
            appt_date += timedelta(days=1)
        day_name = appt_date.strftime("%A")
        preferred_date = appt_date.strftime("%Y-%m-%d")
    
    # Validate time or suggest
    if not preferred_time:
        preferred_time = "10:00 AM"  # Default morning slot
    
    hours = BUSINESS_HOURS.get(day_name, ("9:00 AM", "6:00 PM"))
    
    # Build lead profile
    lead_profile = {
        "name": customer_name,
        "phone": customer_phone,
        "email": customer_email,
        "has_land": has_land,
        "interested_in": interested_in,
        "notes": notes,
        "source": "AI Chat Agent",
        "created_at": datetime.now().isoformat()
    }
    
    appointment = {
        "appointment_id": appointment_id,
        "date": preferred_date,
        "day": day_name,
        "time": preferred_time,
        "location": LOCATION,
        "customer": lead_profile,
        "status": "Confirmed"
    }
    
    return {
        "success": True,
        "message": f"Great news, {customer_name}! Your appointment is confirmed.",
        "appointment": appointment,
        "confirmation_details": (
            f"📅 **Date:** {day_name}, {preferred_date}\n"
            f"🕐 **Time:** {preferred_time}\n"
            f"📍 **Location:** {LOCATION['name']}\n"
            f"📫 **Address:** {LOCATION['address']}\n"
            f"📞 **Phone:** {LOCATION['phone']}\n\n"
            f"We're excited to meet you! Ask for Ben or Mark when you arrive."
        ),
        "reminder": "You'll receive a text reminder 24 hours before your appointment.",
        "land_tip": (
            "Since you mentioned you have land, bring your property details and we can discuss site prep and delivery options!"
            if has_land else
            "Don't have land yet? No problem! We can discuss land-home packages and financing options."
        )
    }


def get_business_hours(
    day: Optional[str] = None,
    tool_context: ToolContext = None
) -> dict:
    """
    Get Texas Home Outlet business hours.
    
    Args:
        day: Specific day to check (e.g., "Monday"), or None for all days
        tool_context: ADK tool context
    
    Returns:
        Dictionary with business hours
    """
    if day and day.capitalize() in BUSINESS_HOURS:
        hours = BUSINESS_HOURS[day.capitalize()]
        return {
            "success": True,
            "day": day.capitalize(),
            "open": hours[0],
            "close": hours[1],
            "location": LOCATION
        }
    
    return {
        "success": True,
        "hours": {
            day: {"open": hours[0], "close": hours[1]} 
            for day, hours in BUSINESS_HOURS.items()
        },
        "location": LOCATION,
        "note": "Stop by anytime! We're conveniently located on FM 1960 in Huffman."
    }
