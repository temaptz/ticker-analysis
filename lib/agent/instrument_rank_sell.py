import os
from typing import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils, db_2, logger, forecasts, invest_calc


class RatePercentWithConclusion(BaseModel):
    rate: int
    final_conclusion: str

class State(TypedDict, total=False):
    human_name: str
    instrument_uid: str
    invest_calc_rate: RatePercentWithConclusion
    price_prediction_rate: RatePercentWithConclusion
    structured_response: RatePercentWithConclusion


def update_recommendations():
    graph_sell = get_sell_rank_graph()

    for i in users.sort_instruments_for_sell(
            instruments_list=users.get_user_instruments_list(account_id=users.get_analytics_account().id)
    ):
        try:
            input_state: State = {
                'human_name': instruments.get_instrument_human_name(i.uid),
                'instrument_uid': i.uid,
            }

            result = graph_sell.invoke(
                input=input_state,
                debug=True,
                config=agent.llm.config,
            )

            if structured_response := result.get('structured_response', None):
                if structured_response.rate:
                    previous_rate = agent.utils.get_sell_rate(instrument_uid=i.uid)

                    db_2.instrument_tags_db.upset_tag(
                        instrument_uid=i.uid,
                        tag_name='llm_sell_rate',
                        tag_value=structured_response.rate,
                    )

                    logger.log_info(
                        message=f'Сохранена оценка продажи {i.name}\nОценка: {structured_response.rate}\nКомментарий: {structured_response.final_conclusion}\nПрошлая оценка: {previous_rate}',
                        is_send_telegram=True,
                    )

                if structured_response.final_conclusion:
                    db_2.instrument_tags_db.upset_tag(
                        instrument_uid=i.uid,
                        tag_name='llm_sell_conclusion',
                        tag_value=structured_response.final_conclusion,
                    )
        except Exception as e:
            logger.log_error(method_name='update_recommendations_item sell', error=e)


def get_sell_rank_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(State)

    graph_builder.add_node('llm_invest_calc_rate', llm_invest_calc_rate)
    graph_builder.add_node('llm_price_prediction_rate', llm_price_prediction_rate)
    graph_builder.add_node('llm_total_sell_rate', llm_total_sell_rate)

    graph_builder.add_edge(START, 'llm_invest_calc_rate')
    graph_builder.add_edge('llm_invest_calc_rate', 'llm_price_prediction_rate')
    graph_builder.add_edge('llm_price_prediction_rate', 'llm_total_sell_rate')
    graph_builder.add_edge('llm_total_sell_rate', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='sell_rank_graph',
    )

    return graph


def llm_invest_calc_rate(state: State):
    result: State = {}

    try:
        if instrument_uid := state.get('instrument_uid', None):
            if calc := invest_calc.get_invest_calc_by_instrument_uid(
                    instrument_uid=instrument_uid,
                    account_id=users.get_analytics_account().id,
            ):
                if p := calc['potential_profit_percent']:
                    def lerp(x, a, b, y0, y1):
                        return y0 + (0 if b == a else (x - a) / (b - a)) * (y1 - y0)

                    if p <= 0:
                        rate = 0
                    elif 0 < p <= 5:
                        rate = round(lerp(p, 0, 5, 11, 29))
                    elif 5 < p <= 10:
                        rate = round(lerp(p, 5, 10, 30, 59))
                    elif 10 < p <= 20:
                        rate = round(lerp(p, 10, 20, 60, 79))
                    elif 20 < p <= 30:
                        rate = round(lerp(p, 20, 30, 80, 89))
                    else:
                        rate = min(100, round(lerp(p, 30, 60, 90, 100)))


                    if rate or rate == 0:
                        result = {
                            'invest_calc_rate': RatePercentWithConclusion(
                                rate=rate,
                                final_conclusion=f'Финальная оценка продажи: {rate} [0-100]. potential_profit_percent: {utils.round_float(calc['potential_profit_percent'], 4)}% - потенциальная выгода в процентах',
                            )
                        }

    except Exception as e:
        logger.log_error(
            method_name='llm_invest_calc_rate',
            error=e,
            is_telegram_send=False,
        )
    return result


def llm_price_prediction_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        prompt = f'''
        # ЗАДАНИЕ
        
        Как специалист по трейдингу проанализируй и оцени насколько потенциально выгодна продажа актива именно сейчас.
        
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй изменение цены на каждом интервале времени, оцени стабильность и направление ожидаемой динамики.
        2. Учитывай что актив выгоднее продавать при высокой цене и перед устойчивым трендом на снижение.
        3. Оцени, насколько выгодна продажа актива именно сейчас.
        4. Продажа выгодна если в ближайший месяц ожидается постепенный стабильный тренд на снижение, чем сильнее снижение, тем выше оценка.
        5. Если в длительной перспективе (6-24 месяца) так же ожидается тренд на снижение цены, то это увеличивает оценку.
        6. Незначительный рост в течении нескольких дней перед стабильным снижением говорит о хорошем моменте для продажи и увеличивает оценку. 
        7. Присвой итоговую числовую оценку выгодной продажи целое число от 0 до 100, где:
           - 0 - все price_prediction до месяца стабильно положительные, продажа в ближайшее время не выгодна;
           - 1-49 - в ближайший месяц присутствуют положительные price_prediction, продажа не рекомендована;
           - 50-74 - все price_prediction до месяца стабильно отрицательные, продажа возможна;
           - 75-89 - все price_prediction до трех месяцев стабильно отрицательные, сейчас хороший момент для продажи.
           - 90-100 - все price_prediction до пол года стабильно отрицательные, сейчас идеальный момент для продажи.
        8. На основе шкалы данной инструкции построй собственную более развернутую шкалу и дай по ней окончательную точную оценку.
        9. В конце кратко обобщи все рассуждение сформулируй итоговый вывод и итоговую оценку целое число от 0 до 100.
        
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''


        print('HUMAN MESSAGE price_prediction', prompt)

        try:
            if result := agent.llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        SystemMessage(content=agent.prompts.get_thinking_prompt()),
                        HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid)),
                        HumanMessage(content=prompt),
                    ],
                    config=agent.llm.config,
            ):
                if result and result.rate is not None and 0 <= result.rate <= 100:
                    logger.log_info(message=f'LLM PRICE PREDICTION RATE IS: {result.rate}')
                    return {'price_prediction_rate': result}

        except Exception as e:
            logger.log_error(
                method_name='llm_price_prediction_rate',
                error=e,
                is_telegram_send=False,
            )

    return {}


def llm_total_sell_rate(state: State) -> State:
    invest_c = state.get('invest_calc_rate', None)
    price_prediction = state.get('price_prediction_rate', None)
    invest_rate = invest_c.rate if (invest_c and invest_c.rate) else None
    invest_rate_conclusion = invest_c.final_conclusion if (invest_c and invest_c.final_conclusion) else None
    price_prediction_rate = price_prediction.rate if (price_prediction and price_prediction.rate) else None
    price_prediction_conclusion = price_prediction.final_conclusion if (price_prediction and price_prediction.final_conclusion) else None

    if invest_rate or price_prediction_rate:
        try:
            weights = {'invest_rate': 2, 'price_prediction_rate': 1}
            calc_rate = int(
                (
                        (invest_rate or 0) * weights['invest_rate']
                        + (price_prediction_rate or 0) * weights['price_prediction_rate']
                )
                / (weights['invest_rate'] + weights['price_prediction_rate'])
            )

            if calc_rate or calc_rate == 0:
                return {'structured_response': RatePercentWithConclusion(
                    rate=calc_rate,
                    final_conclusion=f'{invest_rate_conclusion}\n{price_prediction_conclusion}'
                )}
        except Exception as e:
            print('ERROR llm_total_sell_rate', e)
    return {}
