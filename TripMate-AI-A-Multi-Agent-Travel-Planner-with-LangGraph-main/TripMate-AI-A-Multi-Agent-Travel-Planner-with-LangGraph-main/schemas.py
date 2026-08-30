from typing import TypedDict, Annotated, List, Optional, Dict, Any
import operator
from pydantic import BaseModel, Field
from langchain_core.messages import AnyMessage

class TripIntent(BaseModel):
    destination: str = Field(default="", description="Target destination city or country")
    origin: str = Field(default="DAC", description="Origin city or airport code")
    duration_days: Optional[int] = Field(default=None, description="Trip duration in days")
    budget: Optional[str] = Field(default=None, description="Stated budget or budget tier")
    interests: List[str] = Field(default_factory=list, description="Activities, interests or preferences")
    travelers: Optional[int] = Field(default=1, description="Number of travelers")

class TravelState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    user_query: str
    intent: Dict[str, Any]
    flight_results: str
    hotel_results: str
    itinerary: str
    budget_breakdown: str
    llm_calls: Annotated[int, operator.add]

class TravelRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    is_refinement: Optional[bool] = False

class TravelResponse(BaseModel):
    success: bool
    thread_id: str
    answer: str
    intent: Optional[Dict[str, Any]] = None
    flight_results: Optional[str] = None
    hotel_results: Optional[str] = None
    itinerary: Optional[str] = None
    budget_breakdown: Optional[str] = None
    llm_calls: int = 0
    execution_time_seconds: Optional[float] = None
    cache_stats: Optional[Dict[str, int]] = None
