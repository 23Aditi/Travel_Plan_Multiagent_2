from langchain_core.messages import AIMessage
from tools.flight_tool import search_flights
from schemas import TravelState

def flight_agent(state: TravelState):
    query = state.get("user_query", "")
    intent = state.get("intent", {})
    destination = intent.get("destination", "")
    origin = intent.get("origin", "")
    
    search_prompt = f"Flights from {origin} to {destination}" if destination and origin else query

    try:
        flight_data = search_flights(search_prompt)
        if not flight_data or "No flights found" in flight_data:
            flight_data = search_flights(query)
    except Exception as exc:
        print(f"[flight_agent] Error fetching live flight data: {exc}")
        flight_data = (
            f"Live flight API query encountered a transient issue: {exc}. "
            f"Typical route: Flights from {origin} to {destination} usually operate via major international carriers. "
            "Please check Google Flights or Skyscanner for current live fares."
        )

    return {
        "flight_results": flight_data,
        "messages": [AIMessage(content="Flight options & route intelligence gathered.")],
        "llm_calls": 1
    }
