import json
from pathlib import Path
import traceback
import uvicorn

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from auth import get_db, get_current_user, verify_password, get_password_hash, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from models import User, Trip
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import settings
from schemas import TravelRequest
from graph import run_travel_agent, stream_travel_agent
from tools.cache import tool_cache

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="TripMate AI",
    description="LangGraph Multi-Agent Travel Planner with Parallel Execution & Streaming",
    version="2.1.0"
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": user}
    )

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={})

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request,
            name="login.html", 
            context={"error": "Invalid email or password"}
        )
    
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html", context={})

@app.post("/register")
async def register(
    request: Request,
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if user:
        return templates.TemplateResponse(
            request=request,
            name="register.html", 
            context={"error": "Email already registered"}
        )
    
    hashed_password = get_password_hash(password)
    new_user = User(email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

# --- User Past Trips Endpoints ---

@app.get("/api/trips")
async def get_user_trips(request: Request, db: Session = Depends(get_db)):
    """Retrieve all saved trips for the authenticated user."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"success": False, "error": "Not authenticated"})
    
    trips = db.query(Trip).filter(Trip.user_id == user.id).order_by(Trip.created_at.desc()).all()
    results = []
    for t in trips:
        results.append({
            "id": t.id,
            "destination": t.destination,
            "duration": t.duration or "Flexible",
            "budget": t.budget or "Moderate",
            "travelers": t.travelers or "1 Traveler",
            "created_at": t.created_at.strftime("%b %d, %Y • %H:%M") if t.created_at else "",
            "thread_id": t.thread_id
        })
    return {"success": True, "trips": results}

@app.get("/api/trips/{trip_id}")
async def get_single_trip(trip_id: int, request: Request, db: Session = Depends(get_db)):
    """Retrieve full itinerary and dossier payload for a saved trip."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"success": False, "error": "Not authenticated"})
    
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        return JSONResponse(status_code=404, content={"success": False, "error": "Trip not found"})
    
    try:
        plan_data = json.loads(trip.plan_data)
    except Exception:
        plan_data = {}

    return {
        "success": True,
        "trip": {
            "id": trip.id,
            "destination": trip.destination,
            "duration": trip.duration,
            "budget": trip.budget,
            "travelers": trip.travelers,
            "thread_id": trip.thread_id,
            "created_at": trip.created_at.strftime("%b %d, %Y") if trip.created_at else "",
            "plan_data": plan_data
        }
    }

@app.post("/api/trips/save")
async def save_user_trip(request: Request, db: Session = Depends(get_db)):
    """Save or update a generated trip itinerary for the authenticated user."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"success": False, "error": "Not authenticated"})
    
    try:
        body = await request.json()
        destination = body.get("destination") or "Custom Destination"
        duration = body.get("duration")
        budget = body.get("budget")
        travelers = body.get("travelers")
        prompt = body.get("prompt")
        thread_id = body.get("thread_id")
        plan_data = body.get("plan_data")

        if not plan_data:
            return JSONResponse(status_code=400, content={"success": False, "error": "Plan data is required"})
        
        existing = None
        if thread_id:
            existing = db.query(Trip).filter(Trip.user_id == user.id, Trip.thread_id == thread_id).first()
        
        if existing:
            existing.destination = destination
            if duration: existing.duration = duration
            if budget: existing.budget = budget
            if travelers: existing.travelers = travelers
            existing.plan_data = json.dumps(plan_data)
            db.commit()
            db.refresh(existing)
            return {"success": True, "trip_id": existing.id, "action": "updated"}
        else:
            new_trip = Trip(
                user_id=user.id,
                thread_id=thread_id,
                destination=destination,
                duration=duration,
                budget=budget,
                travelers=travelers,
                prompt=prompt,
                plan_data=json.dumps(plan_data)
            )
            db.add(new_trip)
            db.commit()
            db.refresh(new_trip)
            return {"success": True, "trip_id": new_trip.id, "action": "created"}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.delete("/api/trips/{trip_id}")
async def delete_trip(trip_id: int, request: Request, db: Session = Depends(get_db)):
    """Delete a saved trip."""
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"success": False, "error": "Not authenticated"})
    
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == user.id).first()
    if not trip:
        return JSONResponse(status_code=404, content={"success": False, "error": "Trip not found"})
    
    db.delete(trip)
    db.commit()
    return {"success": True, "message": "Trip deleted"}

@app.post("/api/travel")
def travel_planner(request_data: TravelRequest):
    """Standard synchronous execution endpoint with full metrics."""
    try:
        user_message = request_data.message.strip()
        if not user_message:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Message cannot be empty."}
            )

        result = run_travel_agent(
            user_input=user_message,
            thread_id=request_data.thread_id
        )

        return JSONResponse(
            content={
                "success": True,
                "thread_id": result["thread_id"],
                "answer": result["answer"],
                "intent": result.get("intent", {}),
                "flight_results": result.get("flight_results", ""),
                "hotel_results": result.get("hotel_results", ""),
                "itinerary": result.get("itinerary", ""),
                "budget_breakdown": result.get("budget_breakdown", ""),
                "llm_calls": result.get("llm_calls", 0),
                "execution_time_seconds": result.get("execution_time_seconds"),
                "cache_stats": result.get("cache_stats", {})
            }
        )
    except Exception as e:
        print("ERROR:", e)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/travel/stream")
def travel_planner_stream(request_data: TravelRequest):
    """SSE endpoint streaming live agent progress and final output."""
    user_message = request_data.message.strip()
    if not user_message:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Message cannot be empty."}
        )

    def event_generator():
        try:
            for event in stream_travel_agent(user_message, request_data.thread_id):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            traceback.print_exc()
            error_payload = {"event": "error", "message": str(e)}
            yield f"data: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "TripMate AI Multi-Agent Engine",
        "version": "2.1.0",
        "architecture": "LangGraph Parallel Fan-Out (6 agents)",
        "langsmith_tracing": bool(settings.LANGCHAIN_API_KEY),
        "cache_metrics": tool_cache.stats(),
        "model": settings.GROQ_MODEL
    }

@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(content={})

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )