from typing_extensions import TypedDict
from pydantic import BaseModel, Field
from langgraph.graph.message import add_messages
from typing import Annotated


class AgentFinalResultFormat(BaseModel):
    list: list[str]


# class CorrectPlanResponseFormat(BaseModel):
#     is_plan_done: bool
#     is_plan_step_done: bool
#     updated_steps: list[str]
#     updated_current_step: str


class State(TypedDict, total=False):
    input: str
    steps: list[str]
    current_step: str
    is_plan_step_done: bool
    is_plan_done: bool
    messages: Annotated[list, add_messages]
    last_agent_messages: list[str]
    agent_results: list[str]
    structured_response: AgentFinalResultFormat | None


class CheckPlanResponseFormat(BaseModel):
    is_plan_step_done: bool
    is_plan_done: bool


class CorrectPlanResponseFormat(BaseModel):
    steps: list[str]
    current_step: str


class StateAgent(TypedDict):
    messages: Annotated[list, add_messages]


class PythonExecutionResult(BaseModel):
    """Строгий ответ инструмента run_python_code."""
    ok: bool = Field(..., description='True, если код выполнился без ошибок и тайм-аута')
    output: str = Field(..., description='stdout либо сообщение об ошибке')
