from langchain_core.messages import AIMessage
from tools.tavily_tool import tavily_search
from schemas import TravelState

def hotel_agent(state: TravelState):
    query = state.get("user_query", "")
    intent = state.get("intent", {})
    destination = intent.get("destination", "")
    budget = intent.get("budget", "")
    
    search_query = f"Top rated hotels in {destination} {budget} budget accommodations" if destination else f"Best hotels for {query}"

    try:
        hotel_results = tavily_search(search_query)
    except Exception as exc:
        print(f"[hotel_agent] Error fetching hotel data: {exc}")
        hotel_results = (
            f"Hotel discovery search encountered an issue: {exc}. "
            f"Recommended areas to stay in {destination or 'the destination'}: Central district, "
            "near public transit hubs. Average hotel rates range from budget stays (₹2,000 - ₹4,000/night) "
            "to mid-tier hotels (₹5,000 - ₹12,000/night) and luxury stays (₹18,000+/night)."
        )

    return {
        "hotel_results": hotel_results,
        "messages": [AIMessage(content="Hotel options & accommodation insights discovered.")],
        "llm_calls": 1
    }
