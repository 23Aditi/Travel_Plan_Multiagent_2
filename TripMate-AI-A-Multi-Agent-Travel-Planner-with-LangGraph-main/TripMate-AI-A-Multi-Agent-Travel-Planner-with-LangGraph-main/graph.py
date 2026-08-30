import uuid
import time
from typing import Generator, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage

from config import settings
from schemas import TravelState
from database import get_checkpointer
from tools.cache import tool_cache
from agents import (
    intent_agent,
    flight_agent,
    hotel_agent,
    itinerary_agent,
    budget_agent,
    final_agent,
)

def build_travel_graph():
    graph = StateGraph(TravelState)

    # Register specialized agent nodes
    graph.add_node("intent_agent", intent_agent)
    graph.add_node("flight_agent", flight_agent)
    graph.add_node("hotel_agent", hotel_agent)
    graph.add_node("itinerary_agent", itinerary_agent)
    graph.add_node("budget_agent", budget_agent)
    graph.add_node("final_agent", final_agent)

    # Workflow Orchestration
    graph.add_edge(START, "intent_agent")

    # Parallel Execution: Flight intelligence and Hotel discovery run concurrently
    graph.add_edge("intent_agent", "flight_agent")
    graph.add_edge("intent_agent", "hotel_agent")

    # Fan-in: Itinerary agent waits for both parallel agents to complete
    graph.add_edge("flight_agent", "itinerary_agent")
    graph.add_edge("hotel_agent", "itinerary_agent")

    # Downstream Sequential Refinement
    graph.add_edge("itinerary_agent", "budget_agent")
    graph.add_edge("budget_agent", "final_agent")
    graph.add_edge("final_agent", END)

    checkpointer = get_checkpointer(settings.DATABASE_URL)
    return graph.compile(checkpointer=checkpointer)

travel_graph = build_travel_graph()

def _create_initial_state(user_input: str) -> dict:
    return {
        "messages": [HumanMessage(content=user_input)],
        "user_query": user_input,
        "intent": {},
        "flight_results": "",
        "hotel_results": "",
        "itinerary": "",
        "budget_breakdown": "",
        "llm_calls": 0
    }

def run_travel_agent(user_input: str, thread_id: str | None = None) -> Dict[str, Any]:
    """Synchronous execution returning complete result dictionary with latency telemetry."""
    start_time = time.time()
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {"configurable": {"thread_id": thread_id}}
    
    # Check if this thread already has existing checkpointed state
    try:
        current_state = travel_graph.get_state(config)
        is_existing_thread = bool(current_state and current_state.values)
    except Exception:
        is_existing_thread = False

    if is_existing_thread:
        input_payload = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input
        }
    else:
        input_payload = _create_initial_state(user_input)

    result = travel_graph.invoke(input_payload, config=config)
    execution_time = round(time.time() - start_time, 2)

    final_answer = result["messages"][-1].content if result.get("messages") else ""

    return {
        "thread_id": thread_id,
        "answer": final_answer,
        "intent": result.get("intent", {}),
        "flight_results": result.get("flight_results", ""),
        "hotel_results": result.get("hotel_results", ""),
        "itinerary": result.get("itinerary", ""),
        "budget_breakdown": result.get("budget_breakdown", ""),
        "llm_calls": result.get("llm_calls", 0),
        "execution_time_seconds": execution_time,
        "cache_stats": tool_cache.stats()
    }

def stream_travel_agent(user_input: str, thread_id: str | None = None) -> Generator[Dict[str, Any], None, None]:
    """Yields real-time progress events as each agent finishes its task."""
    start_time = time.time()
    if not thread_id:
        thread_id = f"user_{uuid.uuid4().hex}"

    config = {"configurable": {"thread_id": thread_id}}

    try:
        current_state = travel_graph.get_state(config)
        is_existing_thread = bool(current_state and current_state.values)
    except Exception:
        is_existing_thread = False

    if is_existing_thread:
        input_payload = {
            "messages": [HumanMessage(content=user_input)],
            "user_query": user_input
        }
        state_accumulator = dict(current_state.values)
        state_accumulator["user_query"] = user_input
        state_accumulator.setdefault("messages", []).append(HumanMessage(content=user_input))
    else:
        input_payload = _create_initial_state(user_input)
        state_accumulator = dict(input_payload)

    yield {
        "event": "start",
        "thread_id": thread_id,
        "is_refinement": is_existing_thread,
        "message": "TripMate multi-agent workflow initialized."
    }

    for event in travel_graph.stream(input_payload, config=config):
        for node_name, node_output in event.items():
            for key, val in node_output.items():
                if key == "llm_calls":
                    state_accumulator["llm_calls"] = state_accumulator.get("llm_calls", 0) + val
                elif key == "messages":
                    state_accumulator["messages"] = state_accumulator.get("messages", []) + val
                else:
                    state_accumulator[key] = val
            
            yield {
                "event": "agent_complete",
                "agent": node_name,
                "thread_id": thread_id,
                "elapsed_seconds": round(time.time() - start_time, 2),
                "intent": state_accumulator.get("intent", {}),
                "flight_preview": bool(state_accumulator.get("flight_results")),
                "hotel_preview": bool(state_accumulator.get("hotel_results")),
                "itinerary_preview": bool(state_accumulator.get("itinerary")),
                "budget_preview": bool(state_accumulator.get("budget_breakdown")),
            }

    final_answer = state_accumulator.get("messages", [])[-1].content if state_accumulator.get("messages") else ""
    execution_time = round(time.time() - start_time, 2)

    yield {
        "event": "done",
        "thread_id": thread_id,
        "answer": final_answer,
        "intent": state_accumulator.get("intent", {}),
        "flight_results": state_accumulator.get("flight_results", ""),
        "hotel_results": state_accumulator.get("hotel_results", ""),
        "itinerary": state_accumulator.get("itinerary", ""),
        "budget_breakdown": state_accumulator.get("budget_breakdown", ""),
        "llm_calls": state_accumulator.get("llm_calls", 0),
        "execution_time_seconds": execution_time,
        "cache_stats": tool_cache.stats()
    }
