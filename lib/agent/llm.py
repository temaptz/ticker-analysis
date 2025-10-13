import os
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

if not os.getenv('OLLAMA_MODEL_NAME'):
    raise RuntimeError('OLLAMA_MODEL_NAME is required and must be set (no defaults).')
model_name = os.getenv('OLLAMA_MODEL_NAME')
llm = ChatOllama(
    base_url=f'http://{'ollama' if docker.is_docker() else 'localhost'}:11434',
    model=model_name,
    verbose=True,
    name='llm_ollama',
    num_ctx=16384,
    temperature=0.01,
)
llm_with_tools = llm.bind_tools(tools=tools)
# llm_agent = create_react_agent(
#     llm=llm,
#     tools=tools,
#     prompt=PromptTemplate(template='Ты полезный ИИ ассистент помощник. Отвечай на Русском языке.', input_variables=[]),
# )
config: RunnableConfig = {'configurable': {'thread_id': '1'}}
