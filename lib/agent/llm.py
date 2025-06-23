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

# planner_prompt = ChatPromptTemplate.from_template(
#     '''
#     Для достижения поставленной цели разработайте простой пошаговый план.
#     Этот план должен включать в себя отдельные задания, которые при правильном выполнении приведут к правильному ответу.
#     Не добавляйте никаких лишних шагов.
#     Результатом последнего шага должен быть окончательный ответ.
#     Убедитесь, что на каждом шаге есть вся необходимая информация - не пропускайте шаги.
#     '''
# )
#
# replanner_prompt = ChatPromptTemplate.from_template(
#     '''
#     Для достижения поставленной цели разработайте простой пошаговый план.
#     Этот план должен включать в себя отдельные задания, которые при правильном выполнении приведут к правильному ответу.
#     Не добавляйте никаких лишних шагов.
#     Результатом последнего шага должен быть окончательный ответ.
#     Убедитесь, что на каждом шаге есть вся необходимая информация - не пропускайте шаги.
#
#     Вашей целью было следующее:
#     {input}
#
#     Ваш первоначальный план был таков:
#     {plan}
#
#     В настоящее время вы выполнили следующие действия:
#     {last_steps}
#
#     Соответствующим образом обновите свой план.
#     Если больше не требуется никаких действий и вы можете вернуть результат, сообщите об этом.
#     В противном случае обновите план.
#     Добавляйте в план только те шаги, которые еще предстоит выполнить.
#     Не возвращайте ранее выполненные шаги как часть плана.
#     '''
# )


def create_plan_step(state: models.State):
    planner = load_chat_planner(llm=llm_with_tools)
    prompt = f'''
    Составь план решения задачи:
    {state.get('input', '')}
    Корректировка:
    {get_last_message_content(state)}
    '''
    plan: Plan = planner.plan(inputs={'input': prompt}, config=config)
    next_step = plan.steps[0].value if len(plan.steps) > 0 else None

    print('RESULT CREATE PLAN', next_step)
    utils.output_json(plan)

    input = state.get('input', '')
    messages = state.get('messages', [HumanMessage(input)])

    print('CREATE PLAN CURRENT STEP', state.get('current_step', None))

    if plan:
        return {
            'steps': [i.value if 'value' in i else i for i in plan.steps],
            'current_step': state.get('current_step', next_step),
            'messages': messages + [HumanMessage(next_step)]
        }
    return {
        'messages': messages,
    }


def correct_plan_step(state: models.State):
    prompt = f'''
    Твоя задача скорректировать план с учетом выполненных действий.
    Вот первоначальный запрос:
    {state.get('input', '')}
    Вот текущий план действий:
    {'\n'.join([i.value for i in state.get('steps', [])])}
    Вот только что выполненное действие:
    {state.get('current_step', '')}
    Такой был результат:
    {get_last_message_content(state)}
    Обнови план с учетом выполненных действий и контекста сообщений. А так же определи, выполнен ли весь план и итоговое задание.
    История сообщений:
    {'\n'.join([i.content for i in state.get('messages', [])])}
    '''
    result = llm.with_structured_output(models.CorrectPlanResponseFormat).invoke(
        prompt,
        config=config,
    )

    print('RESULT CORRECT PLAN', result)
    utils.output_json(result)

    if result:
        return {
            'is_plan_done': result.is_plan_done or state.get('is_plan_done', False),
            'is_plan_step_done': result.is_plan_step_done or state.get('is_plan_step_done', False),
            'steps': result.updated_steps or state.get('steps', []),
            'current_step': result.updated_current_step or state.get('current_step', ''),
        }
    return {}


def agent_step(state: models.State):
    result = llm_agent.invoke({'messages': state.get('messages', [])}, config=config)
    print('AGENT RESULT')
    utils.output_json(result)
    return {'messages': state.get('messages', []) + result.get('messages', [])}


def llm_step(state: models.State):
    result = llm.invoke(state.get('messages', []), config=config)
    print('LLM STEP RESULT')
    utils.output_json(result)
    return {'messages': state.get('messages', []) + [result]}


def parse_final_step(state: models.State):
    try:
        llm_structured = llm.with_structured_output(models.AgentFinalResultFormat)
        if result := llm_structured.invoke(state['messages'][-1].content, config=config):
            return {'structured_response': result}
    except Exception as e:
        print('ERROR parse_final', e, state['messages'][-1].content)
    return {'structured_response': None}


def correct_plan_condition_checker(state: models.State):
    if state.get('is_plan_done', False):
        return END

    return '__continue__'


def get_last_message_content(state: models.State) -> str | None:
    if messages := state.get('messages', []):
        if len(messages) > 0 and messages[-1] and messages[-1].content:
            return messages[-1].content
    return None
