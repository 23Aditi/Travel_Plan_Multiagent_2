"""
TripMate AI Backend Module.
This module now serves as a clean bridge to the modular graph orchestration in `graph.py`.
"""

from graph import travel_graph, run_travel_agent, stream_travel_agent
from config import settings
from schemas import TravelState

__all__ = [
    "travel_graph",
    "run_travel_agent",
    "stream_travel_agent",
    "settings",
    "TravelState"
]
