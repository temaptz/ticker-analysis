import os
from langchain_community.chat_models import ChatHuggingFace
from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent
from lib import docker
from lib.agent import agent_tools, models, utils

tools = [
    agent_tools.get_instruments_list,
    agent_tools.get_user_instruments_list,
    agent_tools.get_instrument_info,
    agent_tools.get_instrument_balance,
    agent_tools.get_instrument_buy_rate,
    agent_tools.run_python_code,
]

checkpointer = InMemorySaver()

if not os.getenv('OLLAMA_MODEL_NAME'):
    raise RuntimeError('OLLAMA_MODEL_NAME is required and must be set (no defaults).')
model_name = os.getenv('OLLAMA_MODEL_NAME')
llm = ChatOllama(
    base_url=f'http://{'ollama' if docker.is_docker() else 'localhost'}:11434',
    model=model_name,
    verbose=True, name='llm_ollama',
    num_ctx=16384,
    temperature=0.01,
)
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
