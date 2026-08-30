from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from config import settings
from schemas import TravelState

llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0.3
)

ITINERARY_SYSTEM_PROMPT = """You are an elite itinerary architect and certified travel specialist.
Your goal is to design an engaging, time-optimized, and realistic day-by-day itinerary.

Guidelines:
1. Divide each day into distinct sections: Morning, Afternoon, and Evening.
2. Include specific attractions, local culinary recommendations, and cultural etiquette tips.
3. Keep transit times between activities practical and efficient.
4. Harmonize the itinerary with the provided flight and hotel information.
"""

def itinerary_agent(state: TravelState):
    user_query = state.get("user_query", "")
    intent = state.get("intent", {})
    flights = state.get("flight_results", "None")
    hotels = state.get("hotel_results", "None")
    
    prompt = f"""Design a comprehensive day-by-day travel itinerary.

Trip Details:
- Original Request: {user_query}
- Destination: {intent.get('destination', 'N/A')}
- Duration: {intent.get('duration_days', 'Flexible')} days
- Target Budget Tier: {intent.get('budget', 'Moderate')}
- Focus / Interests: {', '.join(intent.get('interests', []))}

Flight Route Information:
{flights[:1500]}

Accommodations & Locality Context:
{hotels[:1500]}

Generate a balanced, day-by-day breakdown with actionable daily schedules and travel advice."""

    try:
        response = llm.invoke([
            SystemMessage(content=ITINERARY_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        itinerary_content = response.content
    except Exception as exc:
        print(f"[itinerary_agent] Error generating itinerary: {exc}")
        itinerary_content = f"Error generating custom itinerary: {exc}. Please review flight and hotel recommendations."

    return {
        "itinerary": itinerary_content,
        "messages": [AIMessage(content="Day-by-day itinerary generated.")],
        "llm_calls": 1
    }
