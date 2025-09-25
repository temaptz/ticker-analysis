import os
from typing import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils, db_2, logger, forecasts, invest_calc


class State(TypedDict, total=False):
    human_name: str
    instrument_uid: str
    invest_calc_rate: agent.models.RatePercentWithConclusion
    price_prediction_rate: agent.models.RatePercentWithConclusion
    structured_response: agent.models.RatePercentWithConclusion


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
                            'invest_calc_rate': agent.models.RatePercentWithConclusion(
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
        
        Проанализируй прогнозы изменения цены и оцени насколько потенциально выгодна продажа актива именно сейчас.
        
        
        # ПРАВИЛА
        
        1. Продажа выгодна если в ближайший месяц ожидается постепенный стабильный тренд на снижение, чем сильнее снижение, тем выше оценка.
        2. Если в длительной перспективе (6-24 месяца) так же ожидается тренд на снижение цены, то это увеличивает оценку.
        3. Присвой итоговую числовую оценку выгодной продажи целое число от 0 до 100, где:
           - 0 - в ближайший месяц снижения цены не прогнозируется продажа сейчас не выгодна;
           - 50 - в ближайшую неделю прогнозируется начало устойчивого продолжительного тренда на снижение цены сейчас продажа выгодна;
           - 100 - в ближайшие несколько дней прогнозируется начало устойчивого долгосрочного тренда на сильное снижение сейчас идеальный момент для продажи.
        
        
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''

        try:
            if result := agent.llm.llm.with_structured_output(agent.models.RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content='''
                        Ты аналитик фондового рынка эксперт по трендам и тенденциям прогнозов.
                        Твоя задача оценить привлекательность продажи актива по графику прогнозов изменения цены.
                        Используй прогнозы относительного изменения цены на горизонтах 3d,1w,2w,3w,1m,2m,3m,6m,1y.
                        Не выдумывай данные. 
                        Unknown/None отсутствующие данные пропускай и учитывай штрафом.
                        Уверенно давай любые рекомендации. Я внимательно и компетентно проверяю их достоверность.
                        Продажа выгодна в начале устойчивого тренда сильного отрицательного снижения.
                        -20% считается сильным снижением.
                        -1% считается незначительным снижением.
                        '''),
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
                return {'structured_response': agent.models.RatePercentWithConclusion(
                    rate=calc_rate,
                    final_conclusion=f'{invest_rate}\n{invest_rate_conclusion}\n\n{price_prediction_rate}\n{price_prediction_conclusion}'
                )}
        except Exception as e:
            print('ERROR llm_total_sell_rate', e)
    return {}
