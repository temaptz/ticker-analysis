from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from lib import serializer
from lib.agent import agent_tools, models, utils, llm


def get_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('agent', llm.agent)
    graph_builder.add_node('tools', ToolNode(tools=llm.tools))
    graph_builder.add_node('parse_final', llm.parse_final)

    graph_builder.add_edge(START,'agent')
    graph_builder.add_edge('tools', 'agent')
    graph_builder.add_edge('parse_final', END)
    graph_builder.add_conditional_edges(
        source='agent',
        path=tools_condition,
        path_map={'tools': 'tools', END: 'parse_final'},
    )
    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
    )

    return graph


def run():
    graph = get_graph()

    # utils.draw_graph(graph)

    init_state = {'messages': [HumanMessage('Получи список биржевых инструментов. Составь список состоящий из полных названий биржевых инструментов')]}
    result = graph.invoke(
        input=init_state,
        config=llm.config,
    )

    print('RESULT', result)
    print('JSON', utils.output_json(result))
    print('STRUCTURED RESULT', result['structured_response'])
