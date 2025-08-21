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

model_name = 'PetrosStav/gemma3-tools:12b'
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


def agent_step(state: models.State) -> models.State:
    result: models.State = {}

    if current_step := state.get('current_step', None):
        prompt = f'''{current_step}'''

        if response := llm_agent.invoke({'messages': [HumanMessage(content=prompt)]}, config=config):
            if last_agent_messages := response.get('messages', []):
                if len(last_agent_messages) > 0:
                    result['last_agent_messages'] = last_agent_messages

                    if last_message := last_agent_messages[-1]:
                        result['messages'] = [last_message]
                        result['agent_results'] = state.get('agent_results', []) + [last_message.content]

                        print('AGENT SUCCESS RESULT', result)
                        print('APPEND RESULT', last_message.content)

        print('AGENT PROMPT', prompt)
        print('AGENT RESPONSE', response)
        utils.output_json(response)

    return result


def llm_step(state: models.State):
    prompt = f'''
    # ИСХОДНАЯ ЦЕЛЬ
    {state.get('input', 'Unknown')}
    
    # СПИСОК ПРОМЕЖУТОЧНЫХ РЕЗУЛЬТАТОВ
    {get_results_prompt(state)}
    
    # ЗАДАНИЕ
    Сформулируй окончательный результат выполнения действия
    '''
    result: models.State = {
        'messages': [],
    }
    if response := llm.invoke(prompt, config=config):
        result['messages'].append(response)

    return result


def parse_final_step(state: models.State):
    try:
        llm_structured = llm.with_structured_output(models.AgentFinalResultFormat)
        if result := llm_structured.invoke(state['messages'][-1].content, config=config):
            return {'structured_response': result}
    except Exception as e:
        print('ERROR parse_final', e, state['messages'][-1].content)
    return {'structured_response': None}


def get_results_prompt(state: models.State, default ='') -> str:
    if agent_results := state.get('agent_results', None):
        if len(agent_results) > 0:
            result = '\n'.join(f'{n}. {r}' for n, r in enumerate(agent_results, 1))

            return f'\n{result}\n'

    return '[None]'
