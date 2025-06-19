from typing_extensions import TypedDict
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from typing import Annotated


class InvestRecommendationResponse(BaseModel):
    list: list[str]


class StepsResponse(BaseModel):
    tasks_list: list[str]


class State(TypedDict):
    # input: str
    # steps: list[str]
    # current_step: str
    messages: Annotated[list, add_messages]
    structured_response: InvestRecommendationResponse | None

