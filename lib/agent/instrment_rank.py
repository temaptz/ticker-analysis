import datetime
from typing import TypedDict, Annotated

from langchain_core.messages import HumanMessage, AIMessage
from langchain_experimental.plan_and_execute import PlanAndExecute, load_chat_planner, load_agent_executor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from tinkoff.invest import Instrument, StatisticResponse
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils
from lib.agent import models, llm, planner


class FinalResult(BaseModel):
    rate: int


class State(TypedDict, total=False):
    uid: str
    messages: Annotated[list, add_messages]
    instrument: dict
    current_price: float
    fundamental: dict
    balance: int
    consensus_week: float
    consensus_2_weeks: float
    consensus_month: float
    consensus_3_months: float
    consensus_6_months: float
    consensus_year: float
    influence_score_month: float
    influence_score_10_days: float
    structured_response: FinalResult


def run():
    graph = get_graph()
    # agent.utils.draw_graph(graph)
    rates = dict()

    for i in instruments.get_instruments_white_list()[:3]:
        result = graph.invoke(
            input={'uid': i.uid},
            debug=True,
            config=llm.config,
        )

        if structured_response := result.get('structured_response', None):
            if rate := structured_response.rate:
                rates[i.ticker] = rate
                print('STRUCTURED FINAL RATE', rate)

        print('RESULT', result)
        agent.utils.output_json(result)
        print('STRUCTURED RESULT', result.get('structured_response'))

    print('CYCLE RATES', rates)


def get_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(State)

    graph_builder.add_node('collect_data', collect_data)
    graph_builder.add_node('llm_rate', llm_buy_rate)
    graph_builder.add_node('parse_final', parse_final)

    graph_builder.add_edge(START, 'collect_data')
    graph_builder.add_edge('collect_data', 'llm_rate')
    graph_builder.add_edge('llm_rate', 'parse_final')
    graph_builder.add_edge('parse_final', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='instrument_rank_graph',
    )

    return graph


def collect_data(state: State):
    print('COLLECT DATA', state)
    if uid := state.get('uid', None):
        if instrument := instruments.get_instrument_by_uid(uid):
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            current_price = instruments.get_instrument_last_price_by_uid(uid=uid)
            fundamental = (fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument.asset_uid) or [])[0]
            balance = users.get_user_instrument_balance(instrument_uid=instrument.uid)
            consensus_week = predictions.get_relative_predictions_consensus(
                instrument_uid=instrument.uid,
                date_target=now + datetime.timedelta(days=7)
            )
            consensus_2_weeks = predictions.get_relative_predictions_consensus(
                instrument_uid=instrument.uid,
                date_target=now + datetime.timedelta(days=14)
            )
            consensus_month = predictions.get_relative_predictions_consensus(
                instrument_uid=instrument.uid,
                date_target=now + datetime.timedelta(days=30)
            )
            consensus_3_months = predictions.get_relative_predictions_consensus(
                instrument_uid=instrument.uid,
                date_target=now + datetime.timedelta(days=90)
            )
            consensus_6_months = predictions.get_relative_predictions_consensus(
                instrument_uid=instrument.uid,
                date_target=now + datetime.timedelta(days=180)
            )
            consensus_year = predictions.get_relative_predictions_consensus(
                instrument_uid=instrument.uid,
                date_target=now + datetime.timedelta(days=365)
            )
            news_rate_month = news.news.get_influence_score(
                instrument_uid=uid,
                start_date=now - datetime.timedelta(days=30),
                end_date=now,
            )
            news_rate_10_days = news.news.get_influence_score(
                instrument_uid=uid,
                start_date=now - datetime.timedelta(days=10),
                end_date=now,
            )

            return {
                'instrument': serializer.get_dict_by_object_recursive(instrument),
                'current_price': utils.round_float(current_price),
                'fundamental': serializer.get_dict_by_object_recursive(fundamental),
                'balance': balance,
                'consensus_week': utils.round_float(consensus_week),
                'consensus_2_weeks': utils.round_float(consensus_2_weeks),
                'consensus_month': utils.round_float(consensus_month),
                'consensus_3_months': utils.round_float(consensus_3_months),
                'consensus_6_months': utils.round_float(consensus_6_months),
                'consensus_year': utils.round_float(consensus_year),
                'influence_score_10_days': utils.round_float(news_rate_10_days),
                'influence_score_month': utils.round_float(news_rate_month),
            }
    return {}


def llm_buy_rate(state: State):
    instrument_info = ''

    if i := state.get('instrument', None):
        instrument_info += f'''
        # ИНФОРМАЦИЯ ОБ ИНСТРУМЕНТЕ
        
        Название: {i['name'] or 'Unknown'}
        Тикер: {i['ticker'] or 'Unknown'}
        Текущая цена: {state.get('current_price', 'Unknown')}
        '''

    if f := state.get('fundamental', None):
        instrument_info += f'''
        # ФУНДАМЕНТАЛЬНЫЕ ПОКАЗАТЕЛИ
        
        Валюта: {f['currency'] or 'Unknown'}</div>
        Выручка: {f['revenue_ttm'] or 'Unknown'}</div>
        EBITDA: {f['ebitda_ttm'] or 'Unknown'}</div>
        Капитализация: {f['market_capitalization'] or 'Unknown'}</div>
        Долг: {f['total_debt_mrq'] or 'Unknown'}</div>
        EPS — прибыль на акцию: {f['eps_ttm'] or 'Unknown'}</div>
        P/E — цена/прибыль: {f['pe_ratio_ttm'] or 'Unknown'}</div>
        EV/EBITDA — стоимость компании / EBITDA: {f['ev_to_ebitda_mrq'] or 'Unknown'}</div>
        DPR — коэффициент выплаты дивидендов: {f['dividend_payout_ratio_fy'] or 'Unknown'}</div>
        '''

    instrument_info += f'''
    
    # КОНСЕНСУС ПРОГНОЗ ЦЕНЫ
    
    На 1 неделю: {state.get('consensus_week', 'Unknown')}
    На 2 недели: {state.get('consensus_2_weeks', 'Unknown')}
    На 1 месяц: {state.get('consensus_month', 'Unknown')}
    На 3 месяца: {state.get('consensus_3_months', 'Unknown')}
    На 6 месяцев: {state.get('consensus_6_months', 'Unknown')}
    На 1 год: {state.get('consensus_year', 'Unknown')}
    
    # РЕЙТИНГ НОВОСТНОГО ФОНА
    
    На 10 дней: {state.get('influence_score_10_days', 'None')}
    На месяц: {state.get('influence_score_month', 'None')}
    
    # БАЛАНС
    {state.get('balance', 'None')}
    '''

    human_message = HumanMessage(content=f'''
    {instrument_info}
    
    # ЗАДАНИЕ
    Дай оценку от 0 до 100, насколько выгодно сейчас купить этот инструмент с целью дальнейшей продажи.
    
    # ИНСТРУКЦИЯ
    1. Учитывай фундаментальные показатели инструмента.
    2. Учитывай консенсус прогнозы цены инструмента. 
    3. Консенсус прогноз показывает прогноз относительного изменения цены и может быт отрицательными при падении цены.
    4. Учитывай рейтинги новостного фона.
    5. Рейтинг новостного фона показывает оценку влияния новостного фона на инструмент. Может быт отрицательным числом при негативном новостном фоне.
    6. Всесторонне оцени информацию об инструменте и дай однозначную оценку того насколько выгодно сейчас можно купить этот инструмент чтобы потом продать его.
    7. Учитывай оптимальный момент для покупки инструмента.
    8. В ответе должна быть только оценка от 0 до 100. Где 0 - не выгодно, 100 - максимально выгодно.
    9. Учитывай что в дальнейшем оценка будет использоваться для сравнения и выбора инструментов для покупки.
    ''')
    try:
        if result := llm.llm.invoke([human_message], config=llm.config):
            print('LLM RATE RESULT', result)
            print('LLM RATE RESULT CONTENT', result.content)
            agent.utils.output_json(result)

            if content := result.content:
                return {'messages': [human_message, AIMessage(content=content)]}

    except Exception as e:
        print('ERROR llm_buy_rate', e)
    return {}


def parse_final(state: State):
    try:
        llm_structured = llm.llm.with_structured_output(FinalResult)
        if result := llm_structured.invoke(state.get('messages', []), config=llm.config):
            print('FINAL RESULT', result)
            return {'structured_response': result}
    except Exception as e:
        print('ERROR parse_final', e)
    return {}
