from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from lib.agent import agent_tools, models, utils

tools = [
    agent_tools.get_weather,
    agent_tools.get_instruments_list,
    agent_tools.get_user_instruments_list,
    agent_tools.get_instrument_info,
    agent_tools.get_instrument_balance,
]

checkpointer = InMemorySaver()

llm = ChatOllama(model='PetrosStav/gemma3-tools:4b', verbose=True)
llm_agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt='Ты полезный ИИ ассистент помощник. Отвечай на Русском языке.',
    debug=True,
    checkpointer=checkpointer,
)
config: RunnableConfig = {'configurable': {'thread_id': '1'}}

def agent(state: models.State):
    messages = state['messages']
    result = llm_agent.invoke({'messages': messages}, config=config)
    return {'messages': result['messages']}


def parse_final(state: models.State):
    try:
        llm_structured = llm.with_structured_output(models.InvestRecommendationResponse)
        if result := llm_structured.invoke(state['messages'][-1].content, config=config):
            return {'structured_response': result}
    except Exception as e:
        print('ERROR parse_final', e, state['messages'][-1].content)
    return {'structured_response': None}
