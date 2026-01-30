import datetime
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from lib import instruments, users, agent, utils, db_2, logger, invest_calc, date_utils, predictions, learn, serializer


class State(TypedDict, total=False):
    human_name: str
    instrument_uid: str
    invest_calc_rate: agent.models.RatePercentWithConclusion
    price_prediction_rate: agent.models.RatePercentWithConclusion
    macd_sell_rate: agent.models.RatePercentWithConclusion
    structured_response: agent.models.RatePercentWithConclusion


def update_recommendations():
    graph_sell = get_sell_rank_graph()

    for i in users.sort_instruments_for_sell(
            instruments_list=instruments.get_instruments_white_list()
    ):
        if users.get_user_instrument_balance(instrument_uid=i.uid, account_id=users.get_analytics_account().id) > 0:
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
                            message=f'Сохранена оценка продажи {i.name}\nОценка: {structured_response.rate}\nПрошлая оценка: {previous_rate}\nКомментарий:\n{structured_response.final_conclusion}',
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

        else:
            logger.log_info(
                message=f'Удалена оценка продажи {i.ticker}',
                is_send_telegram=False,
            )
            db_2.instrument_tags_db.delete_tag(
                instrument_uid=i.uid,
                tag_name='llm_sell_rate',
            )
            db_2.instrument_tags_db.delete_tag(
                instrument_uid=i.uid,
                tag_name='llm_sell_conclusion',
            )


def get_sell_rank_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(State)

    graph_builder.add_node('invest_calc_rate', invest_calc_rate)
    graph_builder.add_node('price_prediction_rate', price_prediction_rate)
    graph_builder.add_node('macd_sell_rate', macd_sell_rate)
    graph_builder.add_node('total_sell_rate', total_sell_rate)

    graph_builder.add_edge(START, 'invest_calc_rate')
    graph_builder.add_edge('invest_calc_rate', 'price_prediction_rate')
    graph_builder.add_edge('price_prediction_rate', 'macd_sell_rate')
    graph_builder.add_edge('macd_sell_rate', 'total_sell_rate')
    graph_builder.add_edge('total_sell_rate', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='sell_rank_graph',
    )

    return graph


def invest_calc_rate(state: State):
    result: State = {}

    try:
        if instrument_uid := state.get('instrument_uid', None):
            if calc := invest_calc.get_invest_calc_by_instrument_uid(
                    instrument_uid=instrument_uid,
                    account_id=users.get_analytics_account().id,
            ):
                if p := calc['potential_profit_percent']:
                    if p <= 0:
                        rate = 0
                    elif 0 < p <= 5:
                        rate = round(agent.utils.lerp(p, 0, 5, 0, 50))
                    else:
                        rate = min(100, round(agent.utils.lerp(p, 5, 20, 50, 100)))


                    if rate or rate == 0:
                        result = {
                            'invest_calc_rate': agent.models.RatePercentWithConclusion(
                                rate=rate,
                                final_conclusion=serializer.to_json(
                                    {
                                        'invest_calc_rate': rate,
                                        'potential_profit_percent': utils.round_float(calc['potential_profit_percent'], 4),
                                    },
                                    ensure_ascii=False,
                                    is_pretty=True,
                                )
                            )
                        }

    except Exception as e:
        logger.log_error(
            method_name='invest_calc_rate',
            error=e,
            is_telegram_send=False,
        )
    return result


def price_prediction_rate(state: State):
    target_days_distance = 30 * 6
    days_before_positive_prediction = target_days_distance
    predictions_list = []
    is_no_predictions = True

    if instrument_uid := state.get('instrument_uid', None):
        date_from = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=3)
        date_to = date_from + datetime.timedelta(days=target_days_distance)

        for day in date_utils.get_dates_interval_list(
                date_from=date_from,
                date_to=date_to,
                interval_seconds=(3600 * 24 * 7)
        ):
            pred = predictions.get_prediction(
                instrument_uid=instrument_uid,
                date_target=day,
                avg_days=7,
                model_name=learn.model.CONSENSUS,
            )

            predictions_list.append(utils.round_float(pred or 0, 3))

            if pred:
                is_no_predictions = False

                if pred > 0.01:
                    delta_days = (day - date_from).days
                    if delta_days < days_before_positive_prediction:
                        days_before_positive_prediction = delta_days

    final_rate = agent.utils.linear_interpolation(days_before_positive_prediction, 0, target_days_distance, 0, 1)
    rated = 0 if is_no_predictions else int(max(0, min(final_rate, 1)) * 100)

    return {'price_prediction_rate': agent.models.RatePercentWithConclusion(
        rate=rated,
        final_conclusion=serializer.to_json(
            {
                'price_prediction_rate': rated,
                'days_before_positive_prediction': days_before_positive_prediction,
                'predictions': '; '.join(map(str, predictions_list)),
            },
            ensure_ascii=False,
            is_pretty=True,
        )
    )}


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

        print('PRICE PREDICTION SELL PROMPT', prompt)

        try:
            if result := agent.llm.llm.with_structured_output(agent.models.RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.utils.trim_prompt('''
                        Ты аналитик фондового рынка эксперт по трендам и тенденциям прогнозов.
                        Твоя задача оценить привлекательность продажи актива по графику прогнозов изменения цены.
                        Используй прогнозы относительного изменения цены на горизонтах 3d,1w,2w,3w,1m,2m,3m,4m,5m,6m,1y.
                        Не выдумывай данные. 
                        Unknown/None отсутствующие данные пропускай и учитывай штрафом.
                        Уверенно давай рекомендации. Я внимательно и компетентно проверяю их достоверность.
                        Продажа выгодна в начале устойчивого тренда сильного отрицательного снижения.
                        -10% считается сильным снижением.
                        -1% считается незначительным снижением.
                        ''')),
                        HumanMessage(content=agent.utils.trim_prompt(agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid))),
                        HumanMessage(content=agent.utils.trim_prompt(prompt)),
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


def macd_sell_rate(state: State):
    final_rate = 0
    graph_hist = []

    if instrument_uid := state.get('instrument_uid', None):
        if rated := agent.macd.macd_sell_rate(instrument_uid=instrument_uid):
            if rated['rate'] is not None:
                final_rate = rated['rate']
                graph_hist = rated['graph_hist'] or []

    return {'macd_sell_rate': agent.models.RatePercentWithConclusion(
        rate=final_rate,
        final_conclusion=serializer.to_json(
            {
                'final_rate': final_rate,
                'macd_days_hist': '; '.join(map(str, graph_hist)),
            },
            ensure_ascii=False,
            is_pretty=True,
        )
    )}


def total_sell_rate(state: State) -> State:
    invest_c = state.get('invest_calc_rate', None)
    price_prediction = state.get('price_prediction_rate', None)
    macd_rate = state.get('macd_sell_rate', None)
    invest_rate = invest_c.rate if (invest_c and invest_c.rate is not None) else None
    invest_rate_conclusion = invest_c.final_conclusion if (invest_c and invest_c.final_conclusion) else None
    price_prediction_rated = price_prediction.rate if (price_prediction and price_prediction.rate is not None) else None
    price_prediction_conclusion = price_prediction.final_conclusion if (price_prediction and price_prediction.final_conclusion) else None
    macd_rated = macd_rate.rate if (macd_rate and macd_rate.rate is not None) else None
    macd_conclusion = macd_rate.final_conclusion if (macd_rate and macd_rate.final_conclusion) else None

    if invest_rate or price_prediction_rated:
        try:
            weights = {
                'invest_rate': 3,
                'macd_sell_rate': 2,
                'price_prediction_rate': 1,
            }
            calc_rate = int(
                (
                        (invest_rate or 0) * weights['invest_rate']
                        + (price_prediction_rated or 0) * weights['price_prediction_rate']
                        + (macd_rated or 0) * weights['macd_sell_rate']
                )
                / (weights['invest_rate'] + weights['price_prediction_rate'] + weights['macd_sell_rate'])
            )

            if calc_rate or calc_rate == 0:
                return {'structured_response': agent.models.RatePercentWithConclusion(
                    rate=calc_rate,
                    final_conclusion=f'invest: {invest_rate}\n{invest_rate_conclusion}\n\nprice: {price_prediction_rated}\n{price_prediction_conclusion}\n\nmacd: {macd_rated}\n{macd_conclusion}'
                )}
        except Exception as e:
            print('ERROR total_sell_rate', e)
    return {}
