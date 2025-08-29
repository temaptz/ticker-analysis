import math
from typing import TypedDict, Annotated
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils, db_2, logger, telegram, invest_calc
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


def create_orders_2():
    recommendations: list[SellRecommendation] = []

    for instrument in users.sort_instruments_for_sell(
            instruments_list=users.get_user_instruments_list(account_id=users.get_analytics_account().id)
    ):
        if len(recommendations) < 5:
            if sell_rate := agent.utils.get_sell_rate(instrument_uid=instrument.uid):
                if sell_rate > 70:
                    if calc := invest_calc.get_invest_calc_by_instrument_uid(
                            instrument_uid=instrument.uid,
                    ):
                        if calc['potential_profit_percent'] > 3:
                            if rec := get_sell_recommendation_by_uid(
                                instrument_uid=instrument.uid,
                            ):
                                recommendations.append(rec)
                                logger.log_info(message='CREATED SELL RECOMMENDATION', output=rec, is_send_telegram=False)

    for rec in recommendations:
        print('CREATE SELL ORDER FOR', instruments.get_instrument_by_uid(rec.instrument_uid).name)
        print('CREATE SELL ORDER', rec)

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
                name = instruments.get_instrument_human_name(rec.instrument_uid)
                logger.log_info(
                    message=f'Создана заявка на продажу для: "{name}" в количестве: "{rec.qty}" штук по цене: "{price}" рублей',
                    is_send_telegram=True,
                )


def create_orders():
    graph = get_buy_graph()
    # agent.utils.draw_graph(graph)

    if top_instruments := users.sort_instruments_for_sell(
            instruments_list=users.get_user_instruments_list(account_id=users.get_analytics_account().id)
    ):
        available_instruments_uids: list[str] = []

        for instrument in top_instruments:
            if sell_rate := agent.utils.get_sell_rate(instrument_uid=instrument.uid):
                if sell_rate > 70:
                    available_instruments_uids.append(instrument.uid)

        if len(available_instruments_uids) == 0:
            logger.log_info(message='Нет активов для продажи > 70', is_send_telegram=True)
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
                            logger.log_info(
                                message=f'Создана заявка на продажу для: "{instrument.name}" в количестве: "{rec.qty}" штук по цене: "{price}" рублей',
                                is_send_telegram=True,
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
        Создай оптимальную выгодную торговую заявку для продажи актива.
        
        # НАЗВАНИЕ АКТИВА
        human_name: {instruments.get_instrument_human_name(uid=uid)}
        
        # ТЕКУЩАЯ ЦЕНА АКТИВА
        current_price: {instruments.get_instrument_last_price_by_uid(uid=uid)}
        
        # БАЛАНС АКТИВА В ПОРТФЕЛЕ (шт.)
        balance_qty: {users.get_user_instrument_balance(instrument_uid=uid, account_id=users.get_analytics_account().id)}
        
        # ОЦЕНКА ПРИВЛЕКАТЕЛЬНОСТИ ПРОДАЖИ АКТИВА
        sell_rate[0-100]: {agent.utils.get_sell_rate(instrument_uid=uid) or 'Unknown'}
        
        # КОММЕНТАРИЙ ОБ ОЦЕНКЕ ПРИВЛЕКАТЕЛЬНОСТИ ПРОДАЖИ АКТИВА
        sell_rate_conclusion: {agent.utils.get_sell_conclusion(instrument_uid=uid) or 'Unknown'}
        
        # ИНСТРУКЦИЯ
        1. Проанализируй текущую стоимость и прогнозируемые изменения цены актива.
        2. Проанализируй информацию о потенциальной выгоде при продаже.
        3. Проанализируй sell_rate, sell_rate_conclusion.
        4. Продажа должна быть строго выгодной. 
        5. Цена продажи должна быть строго выше средней цены покупки.
        6. Подбери оптимальную выгодную стоимость продажи актива. 
        7. Стоимость продажи должна быть выше текущей рыночной стоимости на 0.5%.
        8. Подбери количество единиц актива, которое сейчас выгодно продать.
        9. Если balance_qty больше единицы, то количество должно быть не больше половины balance_qty.
        10. Если sell_rate меньше 70 то количество должно быть не больше четверти balance_qty.
        '''

        print('RECOMMENDATION CREATE PROMPT', prompt)

        if response := llm.llm.with_structured_output(SellRecommendation).invoke(
                [
                    SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                    SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                    SystemMessage(content=agent.prompts.get_thinking_prompt()),
                    HumanMessage(content=agent.prompts.get_instrument_info_prompt(instrument_uid=uid, is_for_sell=True)),
                    HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=uid, is_for_sell=True)),
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


def get_sell_recommendation_by_uid(instrument_uid: str) -> SellRecommendation or None:
    try:
        target_price = instruments.get_instrument_last_price_by_uid(instrument_uid) * 1.005
        balance_qty = users.get_user_instrument_balance(
            instrument_uid=instrument_uid,
            account_id=users.get_analytics_account().id,
        )
        sell_rate = agent.utils.get_sell_rate(instrument_uid=instrument_uid)
        lot_size = instruments.get_instrument_by_uid(instrument_uid).lot or 1
        qty_calc = balance_qty * 0.01

        if sell_rate > 75:
            qty_calc = balance_qty * 0.10

        if sell_rate > 90:
            qty_calc = balance_qty * 0.50

        qty_round = math.ceil(qty_calc / lot_size) * lot_size

        logger.log_info(
            message='DEBUG SELL RECOMMENDATION',
            output={
                'qty_round': qty_round,
                'qty_calc': qty_calc,
                'lot_size': lot_size,
                'target_price': target_price,
                'is_ok': (0 < qty_round <= qty_calc * 1.5),
            },
            is_send_telegram=True,
        )

        if 0 < qty_round <= qty_calc * 1.5:
            return SellRecommendation(
                instrument_uid=instrument_uid,
                target_price=target_price,
                qty=qty_round,
            )
    except Exception as e:
        print('ERROR get_sell_recommendation_by_uid', e)

    return None
