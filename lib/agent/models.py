from typing_extensions import TypedDict
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from typing import Annotated


class InvestRecommendationResponse(BaseModel):
    recommendation_list: list[dict]


class State(TypedDict):
    messages: Annotated[list, add_messages]
    structured_response: InvestRecommendationResponse | None

