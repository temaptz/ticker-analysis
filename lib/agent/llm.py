import os

from langchain_community.chat_models import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from lib import docker, agent
from langchain_core.globals import set_debug, set_verbose

set_debug(False)
set_verbose(True)

tools = [
    agent.agent_tools.get_instruments_list,
    agent.agent_tools.get_user_instruments_list,
    agent.agent_tools.get_instrument_info,
    agent.agent_tools.get_instrument_balance,
    agent.agent_tools.get_instrument_buy_rate,
    agent.agent_tools.run_python_code,
]

checkpointer = MemorySaver()

model_name = os.getenv('OLLAMA_MODEL_NAME')

llm_local = ChatOllama(
    base_url=f'http://{'ollama' if docker.is_docker() else 'localhost'}:11434',
    model=model_name,
    verbose=True,
    name='llm_ollama',
    num_ctx=16384,
    temperature=0.01,
) if model_name else None

llm_remote = ChatOpenAI(
    base_url=os.getenv('OPENAI_BASE_URL'),
    api_key=os.getenv('OPENAI_API_KEY'),
    model=os.getenv('LLM_MODEL_NAME'),
    verbose=True,
    name='llm_remote',
    temperature=0.1,
) if model_name else None

llm_with_tools = llm_local.bind_tools(tools=tools) if llm_local else None
# llm_agent = create_react_agent(
#     llm=llm,
#     tools=tools,
#     prompt=PromptTemplate(template='Ты полезный ИИ ассистент помощник. Отвечай на Русском языке.', input_variables=[]),
# )
config: RunnableConfig = {'configurable': {'thread_id': '1'}}
