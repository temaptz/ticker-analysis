from typing import TypedDict
from langchain_core.messages import HumanMessage, AIMessage
from langchain_experimental.plan_and_execute import PlanAndExecute, load_chat_planner, load_agent_executor
from langchain_experimental.plan_and_execute.planners.base import LLMPlanner, Plan
from langchain_experimental.plan_and_execute.planners.chat_planner import SYSTEM_PROMPT
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from lib.agent import models, utils, llm


class CheckPlanResponseFormat(BaseModel):
    is_plan_step_done: bool
    is_plan_done: bool


def get_create_plan_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('create_plan', create_plan)

    graph_builder.add_edge(START,'create_plan')
    graph_builder.add_edge('create_plan', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='create_plan_graph',
    )

    return graph


def get_correct_plan_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('correct_plan', correct_plan)

    graph_builder.add_edge(START,'correct_plan')
    graph_builder.add_edge('correct_plan', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='correct_plan_graph',
    )

    return graph


def get_check_plan_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('check_plan', check_plan)

    graph_builder.add_edge(START,'check_plan')
    graph_builder.add_edge('check_plan', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='check_plan_graph',
    )

    return graph


def create_plan(state: models.State):
    result = {}

    planner = load_chat_planner(llm=llm.llm_with_tools)
    prompt = f'''
    Составь план решения следующей задачи:
    {state.get('input', '')}
    '''
    plan: llm.Plan = planner.plan(inputs={'input': prompt}, config=llm.config)

    if len(plan.steps) > 0:
        result['steps'] = [i.value for i in plan.steps]

    return result


def correct_plan(state: models.State):
    result = {}

    if steps := state.get('steps', []):
        current_step = state.get('current_step', '')
        next_step = steps[0]

        if current_step and state.get('is_plan_step_done', False):
            current_step_index = steps.index(current_step)
            if steps[current_step_index + 1]:
                next_step = steps[current_step_index + 1]

        return {
            'current_step': next_step,
            'is_plan_step_done': False,
            'is_plan_done': False,
        }

    return result


def check_plan(state: models.State):
    prompt = f'''
    Твоя задача проверить выполнение плана действий.
    Вот текущий план действий:
    {'\n'.join([i for i in state.get('steps', [])])}
    Вот только что выполненное действие:
    {state.get('current_step', '')}
    Такой был результат:
    {utils.get_last_message_content(state)}
    Проверь, выполнилось ли действие.
    Если действие выполнено, то проверь выполнен ли весь план полностью.
    '''
    result = llm.llm.with_structured_output(CheckPlanResponseFormat).invoke(
        prompt,
        config=llm.config,
    )

    if result:
        return {
            'is_plan_done': result.is_plan_done or False,
            'is_plan_step_done': result.is_plan_step_done or False,
        }
    return {}


def check_plan_condition_checker(state: models.State):
    if state.get('is_plan_done', False):
        return END

    return '__continue__'
