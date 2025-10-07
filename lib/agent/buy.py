import datetime
import math
from typing import TypedDict, Annotated

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, db_2, logger, telegram, utils
from lib.agent import llm


class StructuredList(BaseModel):
    list: list[str]


class BuyRecommendation(BaseModel):
    instrument_uid: str
    target_price: float
    qty: int
    total_price: float


class StructuredResult(BaseModel):
    buy_recommendations: list[BuyRecommendation]


class State(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    instruments_uids: list[str]
    instruments_recommendations: list[BuyRecommendation]
    structured_response: StructuredResult


def create_orders_2():
    recommendations: list[BuyRecommendation] = []

    for instrument in users.sort_instruments_for_buy(
            instruments_list=instruments.get_instruments_white_list()
    ):
        if len(recommendations) < 5:
            if not instrument.for_qual_investor_flag:
                if buy_rate := agent.utils.get_buy_rate(instrument_uid=instrument.uid):
                    if buy_rate >= 70:
                        if rec := get_buy_recommendation_by_uid(
                                instrument_uid=instrument.uid,
                        ):
                            recommendations.append(rec)
                            logger.log_info(message='CREATED BUY RECOMMENDATION', output=rec, is_send_telegram=False)

    for recommendation in recommendations:
        rec: BuyRecommendation = recommendation
        print('CREATE BUY ORDER FOR', instruments.get_instrument_by_uid(rec.instrument_uid).name)
        print('CREATE BUY ORDER', rec)
        if rec.qty > 0:
            price = round(rec.target_price, 1)
            if users.post_buy_order(
                    instrument_uid=rec.instrument_uid,
                    price_rub=price,
                    quantity_lots=utils.get_lots_qty(
                        qty=rec.qty,
                        instrument_lot=instruments.get_instrument_by_uid(rec.instrument_uid).lot
                    ),
            ):
                name = instruments.get_instrument_human_name(rec.instrument_uid)
                logger.log_info(
                    message=f'Создана заявка на покупку v2 для: "{name}" в количестве: "{rec.qty}" штук по цене: "{price}" рублей',
                    is_send_telegram=True,
                )


def create_orders():
    graph = get_buy_graph()
    # agent.utils.draw_graph(graph)

    if top_instruments := users.sort_instruments_for_buy(
            instruments_list=instruments.get_instruments_white_list()
    ):
        available_instruments_uids: list[str] = []

        for instrument in top_instruments[:5]:
            if not instrument.for_qual_investor_flag:
                if buy_rate := agent.utils.get_buy_rate(instrument_uid=instrument.uid):
                    if buy_rate > 50:
                        available_instruments_uids.append(instrument.uid)

        if len(available_instruments_uids) == 0:
            logger.log_info(message='Нет активов для покупки > 50', is_send_telegram=True)
            return

        result = graph.invoke(
            input={'instruments_uids': available_instruments_uids},
            debug=True,
            config=llm.config,
        )

        if rate := result.get('structured_response', None):
            print('STRUCTURED FINAL RATE', rate)

        print('RESULT', result)
        agent.utils.output_json(result)
        print('STRUCTURED RESULT', result.get('structured_response'))
        print('STRUCTURED RESULT RECOMMENDATIONS', result.get('structured_response').buy_recommendations)

        if structured_response := result.get('structured_response', None):
            if recommendations := structured_response.buy_recommendations:
                for recommendation in recommendations:
                    rec: BuyRecommendation = recommendation
                    print('CREATE ORDER FOR', instruments.get_instrument_by_uid(rec.instrument_uid).name)
                    print('CREATE ORDER', rec)
                    if rec.qty > 0:
                        price = round(rec.target_price, 1)
                        if users.post_buy_order(
                            instrument_uid=rec.instrument_uid,
                            price_rub=price,
                            quantity_lots=utils.get_lots_qty(
                                qty=rec.qty,
                                instrument_lot=instruments.get_instrument_by_uid(rec.instrument_uid).lot
                            ),
                        ):
                            instrument = instruments.get_instrument_by_uid(rec.instrument_uid)
                            logger.log_info(
                                message=f'Создана заявка на покупку для: "{instrument.name}" в количестве: "{rec.qty}" штук по цене: "{price}" рублей',
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
        name='buy_graph',
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
        Создай оптимальную и выгодную торговую заявку для покупки актива. 
        Подбери количество актива и цену покупки.
        
        # НАЗВАНИЕ АКТИВА
        human_name: {instruments.get_instrument_human_name(uid=uid)}
        
        # ТЕКУЩАЯ ЦЕНА АКТИВА
        current_price: {instruments.get_instrument_last_price_by_uid(uid=uid)}
        
        # ДОСТУПНО СРЕДСТВ
        balance_rub: {users.get_user_money_rub()}
        
        # ОЦЕНКА ПРИВЛЕКАТЕЛЬНОСТИ ПОКУПКИ АКТИВА
        buy_rate[0-100]: {agent.utils.get_buy_rate(instrument_uid=uid) or 'Unknown'}
        
        # КОММЕНТАРИЙ ОБ ОЦЕНКЕ ПРИВЛЕКАТЕЛЬНОСТИ ПОКУПКИ АКТИВА
        buy_rate_conclusion: {agent.utils.get_buy_conclusion(instrument_uid=uid) or 'Unknown'}
        
        # ИНСТРУКЦИЯ
        1. Проанализируй текущую цену - current_price, баланс - balance_rub, прогнозируемое изменение цены актива - predicted_price, оценку привлекательности покупки актива - buy_rate.
        2. Подбери цену покупки target_price она должна быть на 0.5% ниже current_price.
        3. Подбери общую стоимость покупки total_price учитывая следующие условия:
         - Чем выше buy_rate, тем больше должно быть total_price;
         - Если buy_rate от 70 до 100, то total_price должно быть меньше balance_rub * 0.25;
         - Если buy_rate от 60 до 70, то total_price должно быть меньше balance_rub * 0.15;
         - Если buy_rate от 50 до 60, то total_price должно быть меньше balance_rub * 0.05;
         - Если buy_rate меньше 50, то total_price должно быть меньше balance_rub * 0.03.
        4. Посчитай количество единиц актива qty = total_price / target_price.
        5. Округли qty в большую сторону чтобы оно делилось без остатка на lot_size.
        6. Посчитай новую общую стоимость покупки total_price = target_price * qty.
        7. Установи qty = 0 если не выполняется одно из условий:
         - Если buy_rate от 70 до 100, то total_price должно быть меньше balance_rub * 0.5;
         - Если buy_rate от 60 до 70, то total_price должно быть меньше balance_rub * 0.3;
         - Если buy_rate от 50 до 60, то total_price должно быть меньше balance_rub * 0.2;
         - Если buy_rate меньше 50, то total_price должно быть меньше balance_rub * 0.2.
         8. Желательно чтобы qty > 0. Если qty = 0, то попробуй пройти инструкцию еще раз с учетом полученного опыта, если это не помогло, то оставь qty = 0.
        '''

        print('RECOMMENDATION CREATE PROMPT', prompt)

        if response := llm.llm.with_structured_output(BuyRecommendation).invoke(
                [
                    SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                    SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                    SystemMessage(content=agent.prompts.get_thinking_prompt()),
                    HumanMessage(content=agent.prompts.get_instrument_info_prompt(instrument_uid=uid, is_for_sell=False)),
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


def get_buy_recommendation_by_uid(instrument_uid: str) -> BuyRecommendation or None:
    try:
        target_price = instruments.get_instrument_last_price_by_uid(instrument_uid) * 0.995
        balance_rub = users.get_user_money_rub()
        buy_rate = agent.utils.get_buy_rate(instrument_uid=instrument_uid)
        lot_size = instruments.get_instrument_by_uid(instrument_uid).lot or 1
        total_price_calc = balance_rub * agent.utils.get_buy_balance_multiply(buy_rate=buy_rate)
        qty = max(1, math.ceil(total_price_calc / target_price / lot_size)) * lot_size
        total_price = target_price * qty
        is_ok = (total_price <= total_price_calc * 2)

        logger.log_info(
            message='DEBUG BUY RECOMMENDATION',
            output={
                'qty': qty,
                'lot_size': lot_size,
                'target_price': target_price,
                'total_price_calc': total_price_calc,
                'total_price': total_price,
                'delta_percent': utils.round_float(num=((total_price - total_price_calc) / total_price_calc * 100), decimals=2),
                'is_ok': is_ok,
            },
            is_send_telegram=True,
        )
        
        if is_ok:
            return BuyRecommendation(
                instrument_uid=instrument_uid,
                target_price=target_price,
                qty=qty,
                total_price=total_price,
            )
    except Exception as e:
        print('ERROR get_buy_recommendation_by_uid', e)

    return None
