import json
import re
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_groq import ChatGroq
from config import settings
from schemas import TravelState

llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY,
    temperature=0.1
)

INITIAL_PROMPT = """You are a travel query analysis specialist.
Your task is to parse a natural language trip request and extract structured trip parameters in JSON format.

Output MUST be a valid JSON object matching these exact keys:
{
  "destination": "Name of destination city, region, or country (e.g. 'Tokyo, Japan')",
  "origin": "Origin city or airport code if mentioned, otherwise 'DAC'",
  "duration_days": 7,  // integer number of days, or null if unspecified
  "budget": "Stated budget or budget tier (e.g. '₹50,000', '1.5 Lakhs INR', 'luxury', 'budget'), or 'Moderate' if unspecified",
  "interests": ["sightseeing", "food", "culture"], // list of string interests or activities
  "travelers": 1 // integer number of travelers, default 1
}

Do not include markdown fences or any explanation. Output ONLY the raw JSON string."""

REFINEMENT_PROMPT = """You are a travel query analysis specialist.
The user is updating or refining an existing trip plan.
Given the previous trip parameters and the user's follow-up request, update the parameters while preserving unchanged values.

Output MUST be a valid JSON object matching the exact keys:
destination, origin, duration_days, budget, interests, travelers.

Do not include markdown fences or any explanation. Output ONLY the raw JSON string."""

def intent_agent(state: TravelState):
    query = state.get("user_query", "")
    existing_intent = state.get("intent", {})
    is_refinement = bool(existing_intent and existing_intent.get("destination"))
    
    intent_data = dict(existing_intent) if is_refinement else {
        "destination": query,
        "origin": settings.DEFAULT_ORIGIN_IATA,
        "duration_days": 5,
        "budget": "Moderate",
        "interests": ["sightseeing", "local culture", "food"],
        "travelers": 1
    }
    
    try:
        if is_refinement:
            prompt_content = (
                f"Existing Trip Parameters:\n{json.dumps(existing_intent, indent=2)}\n\n"
                f"User's Refinement Request:\n{query}"
            )
            sys_prompt = REFINEMENT_PROMPT
        else:
            prompt_content = f"Analyze this travel request:\n{query}"
            sys_prompt = INITIAL_PROMPT

        response = llm.invoke([
            SystemMessage(content=sys_prompt),
            HumanMessage(content=prompt_content)
        ])
        
        raw_content = response.content.strip()
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_content, flags=re.MULTILINE).strip()
        
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            intent_data.update(parsed)
    except Exception as exc:
        print(f"[intent_agent] Warning: JSON parsing fallback used ({exc})")

    status_msg = (
        f"Trip parameters refined: {intent_data.get('destination')} ({intent_data.get('duration_days', 'N/A')} days)."
        if is_refinement
        else f"Trip parameters identified: {intent_data.get('destination', 'Destination')} ({intent_data.get('duration_days', 'N/A')} days)."
    )

    return {
        "intent": intent_data,
        "messages": [AIMessage(content=status_msg)],
        "llm_calls": 1
    }
