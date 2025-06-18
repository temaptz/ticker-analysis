from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from lib import serializer
from lib.agent import agent_tools, models, utils


llm = ChatOllama(model='PetrosStav/gemma3-tools:4b', verbose=True)
tools = [
    agent_tools.get_weather,
    agent_tools.get_instruments_list,
    agent_tools.get_user_instruments_list,
    agent_tools.get_instrument_info,
    agent_tools.get_instrument_balance,
]
llm_with_tools = llm.bind_tools(tools=tools)
config: RunnableConfig = {'configurable': {'thread_id': '1'}}

def run():
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('generator', generator)
    graph_builder.add_node('tools', ToolNode(tools=tools))
    graph_builder.add_node('parse_final', parse_final)

    graph_builder.add_edge(START,'generator')
    graph_builder.add_edge('tools', 'generator')
    graph_builder.add_edge('parse_final', END)
    graph_builder.add_conditional_edges(
        source='generator',
        path=tools_condition,
        path_map={'tools': 'tools', END: 'parse_final'},
    )

    graph = graph_builder.compile(checkpointer=checkpointer, debug=True)

    print('GRAPH COMPILED', graph)

    utils.draw_graph(graph)

    result = graph.invoke(
        {'input': 'Получи список биржевых инструментов'},
        config=config,
    )

    print('RESULT', result)
    print('JSON', serializer.to_json(result))
    print('STRUCTURED RESULT', result['structured_response'])


def generator(state: models.State):
    return {'messages': [llm_with_tools.invoke(state['messages'], config=config)]}


def parse_final(state: models.State):
    try:
        llm_structured = llm.with_structured_output(models.InvestRecommendationResponse)
        if result := llm_structured.invoke(state['messages'][-1].content, config=config):
            return {'structured_response': result}
    except Exception as e:
        print('ERROR parse_final', e, state['messages'][-1].content)
    return {'structured_response': None}
