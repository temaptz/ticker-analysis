from typing import TypedDict

from langchain.output_parsers import OutputFixingParser
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_experimental.graph_transformers.llm import system_prompt
from langchain_experimental.plan_and_execute import PlanAndExecute, load_chat_planner, load_agent_executor
from langchain_experimental.plan_and_execute.planners.base import LLMPlanner, Plan
from langchain_experimental.plan_and_execute.planners.chat_planner import SYSTEM_PROMPT
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from lib import serializer
from lib.agent import models, utils, llm


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


def get_execute_current_step_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('execute_step', llm.agent_step)

    graph_builder.add_edge(START,'execute_step')
    graph_builder.add_edge('execute_step', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=False,
        name='execute_step_graph',
    )

    return graph


# def create_plan(input: str) -> list[str]:
#     steps = []
#
#     planner = load_chat_planner(llm=llm.llm_with_tools)
#     prompt = f'''{input}'''
#     plan: llm.Plan = planner.plan(inputs={'input': prompt}, config=llm.config)
#
#     if len(plan.steps) > 0:
#         steps = [i.value for i in plan.steps]
#
#     return steps


def correct_plan(state: models.State) -> models.State:
    prompt = f'''
    # ИСХОДНАЯ ЦЕЛЬ
    {state.get('input', 'Unknown')}
    
    # ТЕКУЩИЙ ПЛАН
    {get_steps_prompt(state.get('steps', []))}
    
    # КОНТЕКСТ ПРОШЛОГО ШАГА
    Выполнявшееся действие: {state.get('current_step', 'None')}
    Успех: {state.get('is_plan_step_done', False)}
    
    # ИНСТРУКЦИЯ
    1. Сначала надо разобраться в задаче, проанализировать ее и разработать план ее решения.
    2. Должен быть заполнен полный план действий, включая уже выполненные шаги.
    3. При необходимости **исправь** план: добавь, удали или скорректируй будущие шаги, чтобы они лучше соответствовали текущему контексту и вели к достижению исходной цели.
    4. Уже выполненные шаги не изменяются.
    5. Если предыдущий шаг успешен, переходи к следующему действию; иначе пересмотри его или предложи альтернативу.
    6. Список шагов в поле steps, каждый шаг содержит понятную инструкцию.
    7. Выбери **current_step** — следующее действие для выполнения из списка шагов. 
    8. Поле current_step должно полностью содержать полную инструкцию достаточную для самостоятельного понимания ИИ-агентом.
    9. Ответ должен быть строго в таком формате JSON: {{"steps": ["шаг 1", "шаг 2", "..."],"current_step": "шаг 1"}}.
    
    # РЕЗУЛЬТАТЫ ВСЕХ ВЫПОЛНЕННЫХ ШАГОВ
    {llm.get_results_prompt(state)}
    '''
    result: models.State = {
        'messages': [],
        'is_plan_step_done': False,
        'is_plan_done': False,
    }

    response = llm.llm_with_tools.invoke(
        [HumanMessage(content=prompt)],
        config=llm.config
    )

    print('CORRECT PLAN PROMPT', prompt)
    print('CORRECT PLAN RESPONSE', response)
    print('CORRECT PLAN RESPONSE CONTENT', response.content)
    utils.output_json(response)

    parser = PydanticOutputParser(pydantic_object=models.CorrectPlanResponseFormat)
    # fixing_parser = OutputFixingParser.from_llm(llm=llm.llm, parser=parser)

    response_parsed: models.CorrectPlanResponseFormat = parser.parse(response.content)

    print('CORRECT PLAN RESPONSE PARSED', response_parsed)
    utils.output_json(response_parsed)

    if response_parsed:
        result['steps'] = response_parsed.steps or state.get('steps', [])
        result['current_step'] = response_parsed.current_step or state.get('current_step', '')
        result['messages'].append(AIMessage(content=serializer.to_json(response_parsed)))

    return result


def check_plan(state: models.State) -> models.State:
    prompt = f'''
    Проверь выполнение плана действий.
    
    # ИСХОДНАЯ ЦЕЛЬ
    {state.get('input', 'Unknown')}
    
    # ТЕКУЩИЙ ПЛАН
    {get_steps_prompt(state.get('steps', []))}
    
    # КОНТЕКСТ ТЕКУЩЕГО ШАГА
    Выполнявшееся действие: {state.get('current_step', 'None')}
    Результат выполнения: {state.get('last_agent_messages', [])[-1].content}
    
    # Инструкция:
    1. Определи, выполнен ли текущий шаг **is_plan_step_done**.
    2. Если результат соответствует и удовлетворяет заданию выполнявшегося действия, то is_plan_step_done = true, иначе false.
    3. В случае сомнений ставь is_plan_step_done = false
    4. Если is_plan_step_done = true и в текущем плане нет следующих действий, установи **is_plan_done = true**, иначе false.
    '''
    result: models.State = {
        'messages': [],
        'is_plan_done': False,
        'is_plan_step_done': False,
    }
    response = llm.llm.with_structured_output(models.CheckPlanResponseFormat).invoke(
        prompt,
        config=llm.config,
    )

    if response:
        result['is_plan_done'] = response.is_plan_done or False
        result['is_plan_step_done'] = response.is_plan_step_done or False
        result['messages'].append(AIMessage(content=serializer.to_json(response)))

    return result


def check_plan_condition_checker(state: models.State):
    if state.get('is_plan_done', False):
        return END

    return '__continue__'


def get_steps_prompt(steps: list[str]) -> str:
    if steps and len(steps) > 0:
        steps_str = ',\n'.join(f'\"{step}\"' for i, step in enumerate(steps, 1))

        if steps_str:
            return f'[{steps_str}]'

    return 'Нет плана'
