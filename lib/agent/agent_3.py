from io import BytesIO
from typing import Annotated
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables.graph import MermaidDrawMethod
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition
from pydantic import BaseModel
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from IPython.display import Image, display
from PIL import Image
from lib import instruments, predictions, news, serializer
from lib.agent import agent_tools, models


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

# prompt = '''
# Получи список биржевых инструментов.
# Проанализируй каждый инструмент в списке и оцени его инвестиционную привлекательность.
# Составь рейтинг из трех самых перспективных инструментов, которые сейчас выгоднее всего купить для продажи в будущем.
# При оценке каждого инструмента используй следующие данные:
# фундаментальные показатели,
# текущая цена,
# прогнозируемое относительное изменение цены
# новостной фон за текущий месяц.
#
# Ответ должен представлять собой json список со следующими полями:
# uid,
# ticker - тикер,
# name - полное название,
# recommendation - рекомендация (BUY/SELL/HOLD),
# description - подробное объяснение рекомендации на русском языке.
# '''

def run():
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(models.State)

    graph_builder.add_node('chatbot', chatbot)
    graph_builder.add_node('tools', ToolNode(tools=tools))
    graph_builder.add_node('parse_final', parse_final)

    graph_builder.add_edge(START,'chatbot')
    graph_builder.add_edge('tools', 'chatbot')
    graph_builder.add_edge('parse_final', END)
    graph_builder.add_conditional_edges(
        source='chatbot',
        path=tools_condition,
        path_map={'tools': 'tools', END: 'parse_final'},
    )

    graph = graph_builder.compile(checkpointer=checkpointer, debug=True)

    print('GRAPH COMPILED', graph)

    draw_graph(graph)

    result = graph.invoke(
        {'messages': [{'role': 'user', 'content': 'Получи список биржевых инструментов'}]},
        config=config,
    )

    print('RESULT', result)
    print('JSON', serializer.to_json(result))
    print('STRUCTURED RESULT', result['structured_response'])


def chatbot(state: models.State):
    return {'messages': [llm_with_tools.invoke(state['messages'], config=config)]}


def parse_final(state: models.State):
    try:
        parser = PydanticOutputParser(pydantic_object=models.InvestRecommendationResponse)
        format_instr = parser.get_format_instructions()
        prompter = PromptTemplate(
            template='{format_instructions}\n\n{content}',
            input_variables=['format_instructions', 'content'],
            partial_variables={'format_instructions': format_instr}
        )
        parsed_obj = prompter | llm_with_tools | parser
        result = parsed_obj.invoke({'content': state['messages'][-1].content})
        return {'structured_response': result}
    except Exception as e:
        print('ERROR parse_final', e, state['messages'][-1].content)
    return {'structured_response': None}


def draw_graph(graph):
    try:
        png_bytes = graph.get_graph().draw_mermaid_png(
            draw_method=MermaidDrawMethod.PYPPETEER
        )
        img = Image.open(BytesIO(png_bytes))
        img.show()

    except Exception as e:
        print('ERROR', e)
        pass
