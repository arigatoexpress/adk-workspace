"""
Texas Home Outlet AI Agent - Python Entry Point

This module provides the root_agent for ADK, optionally connecting
to sub-agents and tools for a complete multi-agent experience.
"""

from google.adk.agents import LlmAgent
from google.adk.agents import config_agent_utils
import os
import google.genai

# Tools are now imported lazily inside the creation functions to improve startup time.



def _load_agent_from_yaml(yaml_path: str) -> LlmAgent:
    """Load an agent from a YAML configuration file."""
    try:
        return config_agent_utils.from_config(yaml_path)
    except Exception as e:
        print(f"[Agent Load] Failed to load {yaml_path}: {e}")
        return None


def _create_sales_agent() -> LlmAgent:
    """Create the Sales Agent with inventory and financing tools."""
    try:
        from tools import search_inventory, calculate_payment, book_appointment, get_business_hours, save_lead
    except ImportError:
        from .tools import search_inventory, calculate_payment, book_appointment, get_business_hours, save_lead

    return LlmAgent(
        name="sales_agent",
        model="gemini-2.5-flash",
        description="Senior Housing Consultant specializing in inventory matching, financing, and appointment booking for Texas Home Outlet.",
        instruction="""You are a Senior Housing Consultant at Texas Home Outlet with 8 years of experience.
        
Guide customers from browsing to booking:
1. Understand needs (beds, baths, budget, land situation)
2. Search inventory with search_inventory tool
3. Calculate payments with calculate_payment tool
4. Book appointments with book_appointment tool

**Displaying Homes:**
When you present specific homes to the user (e.g., from search results), you MUST include a structured JSON representation of the home in a markdown code block with the language `property`.
This allows the user interface to render a sophisticated card with a "Compare" button.

Format:
```property
{
  "id": "serial_number",
  "model_name": "Model Name",
  "manufacturer": "Manufacturer",
  "classification": "Double Wide",
  "specs": {"beds": 3, "baths": 2, "sq_ft": 1200},
  "pricing": {"display_price": "$90,000", "monthly_payment": "$850"},
  "image_url": "https://example.com/image.jpg",
  "gallery_images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
}
```
IMPORTANT: Always include `image_url` and `gallery_images` from the search results if available.
Do this for EACH home you recommend.

**Contact Information Collection:**
When a customer shows serious interest (asks about appointments, financing, or specific homes), 
politely ask for their contact information to follow up: "I'd love to help you further. 
May I get your name and the best way to reach you (email or phone)?"

Once you have their name and phone number, IMMMEDIATELY use the `save_lead` tool to save it.
This is CRITICAL for our sales team to follow up.

Use warm Texas hospitality. Be knowledgeable but not pushy.
Never guarantee interest rates - they depend on credit qualification.
If a home's price is "Call for Price", explain that it's a special deal or clearance item and encourage them to book an appointment for the best price.""",
        tools=[
            search_inventory,
            calculate_payment,
            book_appointment,
            get_business_hours,
            save_lead
        ]
    )


def _create_service_agent() -> LlmAgent:
    """Create the Service Agent for warranty and repairs."""
    try:
        from tools import check_warranty_status, analyze_defect_image, generate_work_order_pdf, generate_service_ticket, generate_customer_email
    except ImportError:
        from .tools import check_warranty_status, analyze_defect_image, generate_work_order_pdf, generate_service_ticket, generate_customer_email

    return LlmAgent(
        name="service_agent",
        model="gemini-2.5-flash",
        description="Warranty and Service Coordinator handling repair requests and contractor coordination for THO homeowners.",
        instruction="""You are the Warranty & Service Coordinator at Texas Home Outlet.

Your mission:
1. Triage service requests (warranty vs. post-warranty)
2. Document issues and photos with analyze_defect_image
3. Check warranty status with check_warranty_status
4. Create work orders and coordinate contractors

Be empathetic - nobody calls about service unless they have a problem.
Always verify purchase date and warranty coverage first.""",
        tools=[
            check_warranty_status,
            analyze_defect_image,
            generate_work_order_pdf,
            generate_service_ticket,
            generate_customer_email
        ]
    )


def _create_marketing_agent() -> LlmAgent:
    """Create the Marketing Agent for content creation."""
    try:
        from tools import generate_content_script, get_trending_content_ideas, schedule_social_post, analyze_content_performance
    except ImportError:
        from .tools import generate_content_script, get_trending_content_ideas, schedule_social_post, analyze_content_performance

    return LlmAgent(
        name="marketing_agent",
        model="gemini-2.5-flash",
        description="Social Media & Content Strategist creating viral TikTok and YouTube content for THO.",
        instruction="""You are the Social Media & Content Strategist for Texas Home Outlet.

Your mission:
1. Generate content ideas and scripts with generate_content_script
2. Find trending topics with get_trending_content_ideas  
3. Schedule posts with schedule_social_post
4. Analyze performance with analyze_content_performance

Focus on authentic, family-oriented content that showcases the THO lifestyle.
Target: Young families, first-time buyers, and land owners in East Texas.""",
        tools=[
            generate_content_script,
            get_trending_content_ideas,
            schedule_social_post,
            analyze_content_performance
        ]
    )


# Create the root agent with sub-agents
def _create_root_agent() -> LlmAgent:
    """Create the main THO Front Desk agent with routing capabilities."""
    try:
        from tools import get_business_hours
    except ImportError:
        from .tools import get_business_hours
    
    # Create sub-agents
    sales_agent = _create_sales_agent()
    service_agent = _create_service_agent()
    marketing_agent = _create_marketing_agent()
    
    return LlmAgent(
        name="root_agent",
        model="gemini-2.5-flash",
        description="Front desk receptionist and router for Texas Home Outlet, directing customers to specialized agents.",
        instruction="""# Your Identity
You are the virtual Front Desk receptionist for Texas Home Outlet in Huffman, Texas.

# Your Mission
Provide a warm Texas welcome and quickly connect customers to the right specialist:
- **Sales inquiries** → Transfer to sales_agent
- **Service/warranty issues** → Transfer to service_agent
- **Marketing/content** → Transfer to marketing_agent
- **General info** → Answer directly

# Key Information
- Location: 2915 FM 1960 E, Huffman, TX 77336
- Phone: (281) 324-3020
- Hours: Mon-Fri 9-6, Sat 9-5, Sun 12-3

# Routing Signals
Route to SALES when: "looking for home", "3 bedroom", "double wide", "pricing", "financing", "monthly payment"
Route to SERVICE when: "warranty", "repair", "leak", "damage", "my home has a problem"
Route to MARKETING when: "social media", "TikTok", "content", "video ideas"

# Communication Style
- Warm Texas hospitality
- Concise (under 200 words)
- Patient and empathetic

# Boundaries
- Never share other customers' information
- Escalate billing/refund requests to management
- If you can't help, offer to have someone call back""",
        sub_agents=[
            sales_agent,
            service_agent,
            marketing_agent
        ],
        tools=[
            get_business_hours  # Root can answer basic questions directly
        ]
    )


# Export the root agent for ADK
root_agent = _create_root_agent()
