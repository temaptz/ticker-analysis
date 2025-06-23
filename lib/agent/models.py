from typing_extensions import TypedDict
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from typing import Annotated


class AgentFinalResultFormat(BaseModel):
    list: list[str]


class CorrectPlanResponseFormat(BaseModel):
    is_plan_done: bool
    is_plan_step_done: bool
    updated_steps: list[str]
    updated_current_step: str


class State(TypedDict):
    input: str
    steps: list[str]
    current_step: str
    is_plan_step_done: bool
    is_plan_done: bool
    messages: Annotated[list, add_messages]
    structured_response: AgentFinalResultFormat | None


class StateAgent(TypedDict):
    messages: Annotated[list, add_messages]
