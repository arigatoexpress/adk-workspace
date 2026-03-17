
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from google.adk.runners import InMemoryRunner
from google.adk.apps import App
from google.adk.sessions import Session
# from google.genai import types # Lazy loaded in run_agent
from root_agent import root_agent
import logging
from structured_logging import logger as struct_logger
from conversation_memory import ConversationMemory
from lead_management import LeadManager, Lead
import time
import uuid
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Vertex AI
# Note: vertexai.init is removed to improve cold start time (saves ~5s).
# The google.genai SDK and ADK should handle config via env vars.
# If explicit init is needed, do it lazily.
# import vertexai
# project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "forwardai-485602")
# location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
# vertexai.init(project=project_id, location=location)

app = FastAPI()

# Initialize conversation memory
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "forwardai-485602")
conversation_memory = ConversationMemory(project_id=project_id)
lead_manager = LeadManager(project_id=project_id)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Runner
# Use a global runner for simplicity.
adk_app = App(name="root_agent", root_agent=root_agent)
runner = InMemoryRunner(app=adk_app)

@app.post("/run")
async def run_agent(request: Request):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        data = await request.json()
        
        user_id = data.get("userId", "default_user")
        session_id = data.get("sessionId", "default_session")
        new_message_dict = data.get("newMessage")
        
        # Construct Content object
        text_content = ""
        if new_message_dict and "parts" in new_message_dict:
            text_content = new_message_dict["parts"][0].get("text", "")
        
        struct_logger.request(request_id, user_id, session_id, text_content)
        
        # Get conversation context
        try:
            context = await conversation_memory.get_context(session_id, user_id)
            context_prompt = context.preferences.to_prompt_context()
            struct_logger.info("Context retrieved", request_id=request_id, has_preferences=bool(context_prompt))
        except Exception as e:
            struct_logger.warning("Context retrieval failed", request_id=request_id, error=str(e))
            context_prompt = ""

        # Create proper Content object expected by ADK
        from google.genai import types
        new_message = types.Content(
            role="user",
            parts=[types.Part(text=text_content)]
        )

        # Ensure session exists
        existing_session = await runner.session_service.get_session(
            app_name="root_agent",
            user_id=user_id,
            session_id=session_id
        )
        
        if not existing_session:
            struct_logger.info("Session created", request_id=request_id, session_id=session_id)
            await runner.session_service.create_session(
                app_name="root_agent",
                user_id=user_id,
                session_id=session_id
            )

        result_generator = runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=new_message
        )
        
        final_text = ""
        
        async for event in result_generator:
            # Aggregate model responses
            if hasattr(event, "content") and event.content and event.content.role == "model":
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text
        
        if not final_text:
            struct_logger.warning("No text generated", request_id=request_id)
            final_text = "I apologize, but I couldn't generate a response. Please try again."

        # Update conversation context with this interaction
        try:
            context = await conversation_memory.update_from_interaction(
                session_id=session_id,
                user_id=user_id,
                user_message=text_content,
                search_results=None  # Could extract from agent response if needed
            )
            struct_logger.info("Context updated", request_id=request_id)
            
            # Auto-create or update lead from conversation context
            try:
                existing_lead = await lead_manager.get_lead_by_session(session_id)
                if existing_lead:
                    # Update existing lead with latest context
                    existing_lead.bedrooms = context.preferences.bedrooms or existing_lead.bedrooms
                    existing_lead.bathrooms = context.preferences.bathrooms or existing_lead.bathrooms
                    existing_lead.budget_max = context.preferences.max_budget or existing_lead.budget_max
                    existing_lead.home_type = context.preferences.home_type or existing_lead.home_type
                    existing_lead.homes_viewed = context.homes_discussed
                    existing_lead.appointment_requested = context.appointment_intent
                    existing_lead.financing_discussed = context.financing_questions > 0
                    await lead_manager.update_lead(existing_lead)
                    struct_logger.info("Lead updated", request_id=request_id, lead_id=existing_lead.lead_id)
                else:
                    # Create new lead if conversation has substance (preferences set or homes discussed)
                    if context.preferences.bedrooms or context.preferences.max_budget or context.homes_discussed:
                        new_lead = Lead(
                            lead_id=f"lead_{session_id[:8]}_{int(time.time())}",
                            user_id=user_id,
                            session_id=session_id,
                            bedrooms=context.preferences.bedrooms,
                            bathrooms=context.preferences.bathrooms,
                            budget_max=context.preferences.max_budget,
                            home_type=context.preferences.home_type,
                            homes_viewed=context.homes_discussed,
                            appointment_requested=context.appointment_intent,
                            financing_discussed=context.financing_questions > 0,
                            source="chat"
                        )
                        await lead_manager.create_lead(new_lead)
                        struct_logger.info("Lead created", request_id=request_id, lead_id=new_lead.lead_id)
            except Exception as e:
                struct_logger.warning("Lead management failed", request_id=request_id, error=str(e))
                
        except Exception as e:
            struct_logger.warning("Context update failed", request_id=request_id, error=str(e))

        duration_ms = (time.time() - start_time) * 1000
        struct_logger.log_analytics_event(
            event_type="INTERACTION_COMPLETE",
            session_id=session_id,
            data={
                "duration_ms": duration_ms,
                "response_length": len(final_text),
                "has_context": bool(context)
            }
        )
        struct_logger.response(request_id, len(final_text), duration_ms)
        
        return {"text": final_text}
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        struct_logger.error("Request failed", request_id=request_id, error=str(e), duration_ms=duration_ms)
        return {"error": str(e)}


@app.get("/leads/export")
async def export_leads(status: str = None):
    """
    Export leads to CSV format
    Query params:
        status: Optional filter by status (new, contacted, qualified, converted)
    """
    try:
        leads = await lead_manager.list_leads(status=status, limit=1000)
        
        if not leads:
            return {"message": "No leads found", "count": 0}
        
        # Convert to CSV format
        import io
        import csv
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        if leads:
            fieldnames = list(leads[0].to_csv_row().keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for lead in leads:
                writer.writerow(lead.to_csv_row())
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=tho_leads_{status or 'all'}_{int(time.time())}.csv"
            }
        )
    except Exception as e:
        struct_logger.error("Lead export failed", error=str(e))
        return {"error": str(e)}, 500


@app.get("/leads/stats")
async def get_lead_stats():
    """Get lead statistics"""
    try:
        all_leads = await lead_manager.list_leads(limit=10000)
        
        stats = {
            "total": len(all_leads),
            "by_status": {},
            "with_contact_info": 0,
            "appointment_requested": 0,
            "financing_discussed": 0
        }
        
        for lead in all_leads:
            # Count by status
            stats["by_status"][lead.status] = stats["by_status"].get(lead.status, 0) + 1
            
            # Count with contact info
            if lead.email or lead.phone:
                stats["with_contact_info"] += 1
            
            # Count appointment requests
            if lead.appointment_requested:
                stats["appointment_requested"] += 1
            
            # Count financing discussions
            if lead.financing_discussed:
                stats["financing_discussed"] += 1
        
        return stats
    except Exception as e:
        struct_logger.error("Lead stats failed", error=str(e))
        return {"error": str(e)}, 500


@app.get("/health")
def health():
    return {"status": "ok"}

# Proxy for session creation if needed
@app.post("/apps/{app_name}/users/{user_id}/sessions/{session_id}")
async def create_session(app_name: str, user_id: str, session_id: str):
    logger.info(f"Creating session: {session_id} for user: {user_id}")
    try:
        await runner.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id
        )
        return {"status": "created", "session_id": session_id}
    except Exception as e:
         logger.error(f"Error creating session: {str(e)}")
         return {"status": "error", "message": str(e)}

# Serve Frontend - Must be last to avoid catching API routes
# Mount assets
app.mount("/assets", StaticFiles(directory="frontend_build/assets"), name="assets")

# Serve index.html for root and unknown routes (SPA support)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("frontend_build/index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
