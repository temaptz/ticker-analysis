from langchain_core.messages import HumanMessage
from langchain_experimental.plan_and_execute import PlanAndExecute, load_chat_planner, load_agent_executor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from lib.agent import models, utils, llm


def get_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('create_plan_step', llm.create_plan_step)
    graph_builder.add_node('llm_agent', llm.llm_agent)
    graph_builder.add_node('check_plan_step', llm.check_plan_step)
    graph_builder.add_node('parse_final_step', llm.parse_final_step)

    graph_builder.add_edge(START,'create_plan_step')
    graph_builder.add_edge('create_plan_step', 'llm_agent')
    graph_builder.add_edge('llm_agent', 'check_plan_step')
    graph_builder.add_edge('parse_final_step', END)

    graph_builder.add_conditional_edges(
        source='check_plan_step',
        path=llm.correct_plan_condition_checker,
        path_map={'__continue__': 'plan_step', END: 'parse_final_step'},
    )

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='llm_agent',
    )

    return graph


def get_plan_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('create_plan_step', llm.create_plan_step)
    graph_builder.add_node('llm_agent', llm.llm_agent)
    graph_builder.add_node('llm', llm.llm_step)
    graph_builder.add_node('correct_plan_step', llm.correct_plan_step)
    graph_builder.add_node('parse_final_step', llm.parse_final_step)

    graph_builder.add_edge(START,'create_plan_step')
    graph_builder.add_edge('create_plan_step', 'llm_agent')
    graph_builder.add_edge('llm_agent', 'correct_plan_step')
    graph_builder.add_edge('llm', 'parse_final_step')
    graph_builder.add_edge('parse_final_step', END)

    graph_builder.add_conditional_edges(
        source='correct_plan_step',
        path=llm.correct_plan_condition_checker,
        path_map={'__continue__': 'create_plan_step', END: 'llm'},
    )

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='llm_agent',
    )

    return graph

def get_main_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)
    graph_builder.add_node('main_node', get_plan_graph())
    graph_builder.add_edge(START, 'main_node')
    graph_builder.add_edge('main_node', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        name='main_node',
        debug=True,
    )

    return graph


def run():
    graph = get_main_graph()
    utils.draw_graph(graph)
    i = {'input': 'Получи список биржевых инструментов. Для каждого инструмента получи полное название. Составь список состоящий из полных названий биржевых инструментов.'}
    result = graph.invoke(
        input=i,
        config=llm.config,
        debug=True,
    )

    print('RESULT', result)
    print('JSON', utils.output_json(result))
    print('STRUCTURED RESULT', result['structured_response'])
