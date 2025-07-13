from langchain.chains.llm import LLMChain
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_experimental.plan_and_execute.planners.base import LLMPlanner, Plan
from langchain_experimental.plan_and_execute.planners.chat_planner import SYSTEM_PROMPT
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from langgraph.constants import END
from lib.agent import agent_tools, models, utils
from langchain_experimental.plan_and_execute import load_chat_planner

tools = [
    agent_tools.get_weather,
    agent_tools.get_instruments_list,
    agent_tools.get_user_instruments_list,
    agent_tools.get_instrument_info,
    agent_tools.get_instrument_balance,
]

checkpointer = InMemorySaver()

llm = ChatOllama(model='PetrosStav/gemma3-tools:4b', verbose=True, name='llm_ollama')
llm_with_tools = llm.bind_tools(tools=tools)
llm_agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt='Ты полезный ИИ ассистент помощник. Отвечай на Русском языке.',
    debug=True,
    checkpointer=checkpointer,
    name='llm_agent',
)
config: RunnableConfig = {'configurable': {'thread_id': '1'}}


def agent_step(state: models.State):
    result = llm_agent.invoke({'messages': state.get('messages', [])}, config=config)
    return {'messages': state.get('messages', []) + result.get('messages', [])}


def llm_step(state: models.State):
    result = llm.invoke(state.get('messages', []), config=config)
    return {'messages': state.get('messages', []) + [result]}


def parse_final_step(state: models.State):
    try:
        llm_structured = llm.with_structured_output(models.AgentFinalResultFormat)
        if result := llm_structured.invoke(state['messages'][-1].content, config=config):
            return {'structured_response': result}
    except Exception as e:
        print('ERROR parse_final', e, state['messages'][-1].content)
    return {'structured_response': None}


# def correct_plan_condition_checker(state: models.State):
#     if state.get('is_plan_done', False):
#         return END
#
#     return '__continue__'


# def get_last_message_content(state: models.State) -> str | None:
#     if messages := state.get('messages', []):
#         if len(messages) > 0 and messages[-1] and messages[-1].content:
#             return messages[-1].content
#     return None
