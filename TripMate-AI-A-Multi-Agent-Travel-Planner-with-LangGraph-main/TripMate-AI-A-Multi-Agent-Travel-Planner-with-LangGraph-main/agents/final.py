from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from config import settings
from schemas import TravelState

llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0.3
)

FINAL_SYSTEM_PROMPT = """You are the Lead Travel Concierge and Senior Planner at TripMate AI.
Your responsibility is to synthesize all research, flight intelligence, hotel options, itinerary schedules, and budget analyses into an exquisite, professional travel dossier.

CRITICAL CURRENCY INSTRUCTION:
All monetary figures, budget amounts, daily costs, hotel room rates, and financial tables MUST be denominated in Indian Rupees (₹ / INR).
Convert any international expenses into Indian Rupees (₹) using realistic exchange rates. Never display totals in USD ($); always use ₹ (INR).

Formatting Requirements:
Format your answer with standard markdown using clear headers:
# 🌍 Trip Dossier: [Destination Name]

## 1. Executive Trip Summary
(Key facts: Destination, Duration, Best time to visit, Vibe, Target Budget in ₹)

## 2. Flight Options & Route Intelligence
(Routes, carriers, connection tips, airport transfer guidance, estimated fares in ₹)

## 3. Recommended Stays & Neighborhoods
(Curated accommodation tiers, best neighborhoods, nightly rates in ₹)

## 4. Day-by-Day Travel Itinerary
(The full structured day-by-day plan with morning/afternoon/evening activities and daily food/transit allowance in ₹)

## 5. Itemized Financial Breakdown
(Comprehensive cost table in Indian Rupees ₹, category totals, and practical money-saving advice in ₹)

## 6. Pre-Departure Checklist & Local Secrets
(Visa requirements reminder, currency exchange advice from INR, packing essentials, local customs)

Ensure the tone is warm, professional, encouraging, and highly practical."""

def final_agent(state: TravelState):
    user_query = state.get("user_query", "")
    intent = state.get("intent", {})
    flights = state.get("flight_results", "")
    hotels = state.get("hotel_results", "")
    itinerary = state.get("itinerary", "")
    budget = state.get("budget_breakdown", "")

    prompt = f"""Synthesize the complete travel dossier in Indian Rupees (₹ / INR) for this request:

User Request: {user_query}
Extracted Intent: {intent}

--- FLIGHT FINDINGS ---
{flights}

--- HOTEL FINDINGS ---
{hotels}

--- ITINERARY DRAFT ---
{itinerary}

--- BUDGET BREAKDOWN (IN RUPEES ₹) ---
{budget}

Assemble everything into the final polished dossier adhering strictly to the requested structure, with all financial calculations in Indian Rupees (₹)."""

    try:
        response = llm.invoke([
            SystemMessage(content=FINAL_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        final_answer = response.content
    except Exception as exc:
        print(f"[final_agent] Error formatting dossier: {exc}")
        final_answer = f"# AI Travel Plan\n\n## Itinerary\n{itinerary}\n\n## Budget (₹)\n{budget}\n\n## Flights\n{flights}\n\n## Hotels\n{hotels}"

    return {
        "messages": [AIMessage(content=final_answer)],
        "llm_calls": 1
    }
