from typing import TypedDict

from langchain_core.messages import HumanMessage
from langchain_experimental.plan_and_execute import PlanAndExecute, load_chat_planner, load_agent_executor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from lib.agent import models, utils, llm, planner


def get_plan_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('create_plan', planner.get_create_plan_graph())
    graph_builder.add_node('correct_plan', planner.get_correct_plan_graph())
    graph_builder.add_node('llm_agent', llm.agent_step)
    graph_builder.add_node('llm', llm.llm_step)
    graph_builder.add_node('check_plan', planner.get_check_plan_graph())
    graph_builder.add_node('parse_final', llm.parse_final_step)

    graph_builder.add_edge(START,'create_plan')
    graph_builder.add_edge('create_plan', 'correct_plan')
    graph_builder.add_edge('correct_plan', 'llm_agent')
    graph_builder.add_edge('llm_agent', 'check_plan')
    graph_builder.add_edge('llm', 'parse_final')
    graph_builder.add_edge('parse_final', END)

    graph_builder.add_conditional_edges(
        source='check_plan',
        path=planner.check_plan_condition_checker,
        path_map={'__continue__': 'correct_plan', END: 'llm'},
    )

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='plan_graph',
    )

    return graph


def run():
    graph = get_plan_graph()
    utils.draw_graph(graph)

    prompt = 'Получи список биржевых инструментов. Для каждого инструмента получи полное название. Составь список состоящий из полных названий биржевых инструментов.'

    result = graph.invoke(
        input={'input': prompt},
        config=llm.config,
        debug=True,
    )

    print('RESULT', result)
    utils.output_json(result)
    print('STRUCTURED RESULT', result.get('structured_response'))
