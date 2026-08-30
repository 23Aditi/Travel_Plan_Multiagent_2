from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from config import settings
from schemas import TravelState

llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0.2
)

BUDGET_SYSTEM_PROMPT = """You are an expert financial travel analyst and budgeting specialist.
Your job is to provide a realistic, itemized financial forecast and budget audit for a trip.

CRITICAL CURRENCY INSTRUCTION:
All pricing, cost estimations, itemized tables, daily allowances, flight costs, hotel rates, and totals MUST be denominated in Indian Rupees (₹ / INR).
If the destination is international (e.g. Japan, Europe, Dubai, USA), convert local expenses into Indian Rupees (₹) using realistic exchange rates. Never output in US Dollars or Euros; use ₹ (INR) exclusively.

Produce:
1. Itemized Category Breakdown in Indian Rupees (₹):
   - Estimated Flights (round trip in ₹)
   - Accommodation (per night & total for duration in ₹)
   - Food & Dining (daily allowance & total in ₹)
   - Local Transportation (metro, cabs, passes in ₹)
   - Sightseeing, Activities & Entrance Fees in ₹
   - Contingency / Buffer (10-15% in ₹)
2. Total Forecast vs. User Target Budget (in ₹): State clearly whether the budget is comfortable, tight, or requires adjustments.
3. 3-4 High-impact Money Saving Strategies in Rupees.
Format the output cleanly in Markdown tables and bullet points."""

def budget_agent(state: TravelState):
    intent = state.get("intent", {})
    itinerary = state.get("itinerary", "")
    flights = state.get("flight_results", "")
    hotels = state.get("hotel_results", "")
    
    prompt = f"""Calculate an itemized travel budget in Indian Rupees (₹ / INR) based on the following:

Trip Context:
- Destination: {intent.get('destination', 'Destination')}
- Origin: {intent.get('origin', settings.DEFAULT_ORIGIN_IATA)}
- Duration: {intent.get('duration_days', 5)} days
- Number of Travelers: {intent.get('travelers', 1)}
- Stated Budget / Tier: {intent.get('budget', 'Moderate')}

Flight Intelligence:
{flights[:1000]}

Hotel & Lodging Data:
{hotels[:1000]}

Planned Activities Summary:
{itinerary[:1000]}

Provide the comprehensive financial breakdown in Indian Rupees (₹)."""

    try:
        response = llm.invoke([
            SystemMessage(content=BUDGET_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        budget_content = response.content
    except Exception as exc:
        print(f"[budget_agent] Error estimating budget: {exc}")
        budget_content = (
            f"Budget breakdown calculation encountered an issue: {exc}. "
            "Estimated average cost: ₹4,000 - ₹8,000/day per person for mid-range travel."
        )

    return {
        "budget_breakdown": budget_content,
        "messages": [AIMessage(content="Financial forecast in Indian Rupees (₹) calculated.")],
        "llm_calls": 1
    }
