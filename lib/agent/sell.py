import datetime
from typing import TypedDict, Annotated

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_experimental.plan_and_execute import PlanAndExecute, load_chat_planner, load_agent_executor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from tinkoff.invest import Instrument, StatisticResponse
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils, db_2, logger, telegram
from lib.agent import models, llm, planner, instrument_rank_buy


class StructuredList(BaseModel):
    list: list[str]


class SellRecommendation(BaseModel):
    instrument_uid: str
    target_price: float
    qty: int


class StructuredResult(BaseModel):
    sell_recommendations: list[SellRecommendation]


class State(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    instruments_uids: list[str]
    instruments_recommendations: list[SellRecommendation]
    structured_response: StructuredResult


def create_orders():
    graph = get_buy_graph()
    # agent.utils.draw_graph(graph)

    if top_instruments := users.sort_instruments_for_sell(
            instruments_list=users.get_user_instruments_list(account_id=users.get_analytics_account().id)
    ):
        available_instruments_uids: list[str] = []

        for instrument in top_instruments:
            if tag := db_2.instrument_tags_db.get_tag(instrument_uid=instrument.uid, tag_name='llm_sell_rate'):
                if tag.tag_value and int(tag.tag_value) > 75:
                    available_instruments_uids.append(instrument.uid)

        if len(available_instruments_uids) == 0:
            print('NO AVAILABLE INSTRUMENTS')
            return

        result = graph.invoke(
            input={'instruments_uids': available_instruments_uids[:3]},
            debug=True,
            config=llm.config,
        )

        if rate := result.get('structured_response', None):
            print('STRUCTURED FINAL RATE', rate)

        print('RESULT', result)
        agent.utils.output_json(result)
        print('STRUCTURED RESULT', result.get('structured_response'))
        print('STRUCTURED RESULT RECOMMENDATIONS', result.get('structured_response').sell_recommendations)

        if structured_response := result.get('structured_response', None):
            if recommendations := structured_response.sell_recommendations:
                for recommendation in recommendations:
                    rec: SellRecommendation = recommendation
                    print('CREATE ORDER FOR', instruments.get_instrument_by_uid(rec.instrument_uid).name)
                    print('CREATE ORDER', rec)

                    if rec.qty > 0:
                        price = round(rec.target_price, 1)

                        if users.post_sell_order(
                            instrument_uid=rec.instrument_uid,
                            price_rub=price,
                                quantity_lots=utils.get_lots_qty(
                                    qty=rec.qty,
                                    instrument_lot=instruments.get_instrument_by_uid(rec.instrument_uid).lot
                                ),
                        ):
                            instrument = instruments.get_instrument_by_uid(rec.instrument_uid)
                            telegram.send_message(
                                message=f'Создана заявка на продажу для: "{instrument.name}" в количестве: "{rec.qty}" штук по цене: "{price}" рублей'
                            )


def get_buy_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(State)

    graph_builder.add_node('instrument_recommendation_create', instrument_recommendation_create)
    graph_builder.add_node('final_parser', final_parser)

    graph_builder.add_edge(START, 'instrument_recommendation_create')
    graph_builder.add_edge('final_parser', END)

    graph_builder.add_conditional_edges(
        'instrument_recommendation_create',
        should_continue_recommendations,
        {'__continue__': 'instrument_recommendation_create', END: 'final_parser'},
    )

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='sell_graph',
    )

    return graph


def should_continue_recommendations(state: State) -> str:
    instruments_list = state.get('instruments_uids', [])
    recommendations_list = state.get('instruments_recommendations', [])

    if len(instruments_list) < 1 or len(instruments_list) == len(recommendations_list):
        print('SHOULD CONTINUE END', len(instruments_list), len(recommendations_list))
        return END

    print('SHOULD CONTINUE CONTINUE', len(instruments_list), len(recommendations_list))
    return '__continue__'


def instrument_recommendation_create(state: State) -> State:
    result: State = {}
    instruments_list = state.get('instruments_uids', [])
    recommendations_list = state.get('instruments_recommendations', [])
    uid = instruments_list[len(recommendations_list)]

    if uid:
        prompt = f'''
        # ЗАДАНИЕ
        Ты специалист по биржевой торговле. 
        Создай оптимальную выгодную торговую заявку для продажи инструмента.
        
        # БАЛАНС ИНСТРУМЕНТА В ПОРТФЕЛЕ (шт.)
        {users.get_user_instrument_balance(instrument_uid=uid, account_id=users.get_analytics_account().id)}
        
        # ИНСТРУКЦИЯ
        1. Проанализируй текущую стоимость и прогнозируемые изменения цены инструмента.
        2. Проанализируй информацию о потенциальной выгоде при продаже.
        3. Продажа должна быть строго выгодной. 
        4. Цена продажи должна быть строго выше средней цены покупки.
        5. Подбери оптимальную выгодную стоимость продажи инструмента. 
        6. Стоимость продажи должна быть выше текущей рыночной стоимости на 2.5%.
        7. Подбери количество единиц инструмента, которое сейчас выгодно продать.
        8. Если баланс больше единицы, то количество должно быть не больше половины баланса.
        '''

        print('RECOMMENDATION CREATE PROMPT', prompt)

        if response := llm.llm.with_structured_output(SellRecommendation).invoke(
                [
                    SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                    SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                    SystemMessage(content=agent.prompts.get_thinking_prompt()),
                    HumanMessage(content=agent.prompts.get_instrument_info_prompt(instrument_uid=uid)),
                    HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=uid)),
                    HumanMessage(content=agent.prompts.get_fundamental_prompt(instrument_uid=uid)),
                    HumanMessage(content=agent.prompts.get_profit_calc_prompt(instrument_uid=uid)),
                    HumanMessage(content=prompt),
                ],
                config=llm.config,
        ):
            print('RECOMMENDATION CREATE RESPONSE', response)
            agent.utils.output_json(response)
            result['instruments_recommendations'] = recommendations_list + [response]

    return result


def final_parser(state: State) -> State:
    result: State = {}

    if response := llm.llm.with_structured_output(StructuredResult).invoke(
            [HumanMessage(content=serializer.to_json(i)) for i in state.get('instruments_recommendations', [])],
            config=llm.config
    ):
        result['structured_response'] = response
        print('FINAL PARSED RESULT', response)
        agent.utils.output_json(response)

    return result
