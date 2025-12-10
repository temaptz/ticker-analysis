import datetime
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from lib import instruments, users, agent, db_2, logger, date_utils, predictions, learn, utils, news, serializer


class State(TypedDict, total=False):
    human_name: str
    instrument_uid: str
    fundamental_rate: agent.models.RatePercentWithConclusion
    price_prediction_rate: agent.models.RatePercentWithConclusion
    news_rate: agent.models.RatePercentWithConclusion
    structured_response: int


def update_recommendations():
    graph_buy = get_buy_rank_graph()

    for i in users.sort_instruments_for_buy(
            instruments_list=instruments.get_instruments_white_list()
    ):

        try:
            if not i.for_qual_investor_flag:
                input_state: State = {
                    'human_name': instruments.get_instrument_human_name(i.uid),
                    'instrument_uid': i.uid,
                }

                result = graph_buy.invoke(
                    input=input_state,
                    debug=True,
                    config=agent.llm.config,
                )

                if structured_response := result.get('structured_response', None):
                    if structured_response.rate:
                        previous_rate = agent.utils.get_buy_rate(instrument_uid=i.uid)

                        db_2.instrument_tags_db.upset_tag(
                            instrument_uid=i.uid,
                            tag_name='llm_buy_rate',
                            tag_value=structured_response.rate,
                        )

                        logger.log_info(
                            message=f'Сохранена оценка покупки {i.name}\nОценка: {structured_response.rate}\nПрошлая оценка: {previous_rate}\nКомментарий:\n{structured_response.final_conclusion}',
                            is_send_telegram=True,
                        )

                    if structured_response.final_conclusion:
                        db_2.instrument_tags_db.upset_tag(
                            instrument_uid=i.uid,
                            tag_name='llm_buy_conclusion',
                            tag_value=structured_response.final_conclusion,
                        )
        except Exception as e:
            logger.log_error(method_name='update_recommendations_item buy', error=e)


def get_buy_rank_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(State)

    graph_builder.add_node('llm_fundamental_rate', llm_fundamental_rate)
    graph_builder.add_node('llm_price_prediction_rate', price_prediction_rate)
    graph_builder.add_node('llm_news_rate', news_rate)
    graph_builder.add_node('llm_total_buy_rate', total_buy_rate)

    graph_builder.add_edge(START, 'llm_fundamental_rate')
    graph_builder.add_edge('llm_fundamental_rate', 'llm_price_prediction_rate')
    graph_builder.add_edge('llm_price_prediction_rate', 'llm_news_rate')
    graph_builder.add_edge('llm_news_rate', 'llm_total_buy_rate')
    graph_builder.add_edge('llm_total_buy_rate', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='buy_rank_graph',
    )

    return graph


def llm_fundamental_rate(state: State):
    if uid := state.get('instrument_uid', None):
        prompt = f'''
        # ЗАДАНИЕ
        
        Проанализируй фундаментальные показатели компании и дай оценку от 0 до 100, 
        насколько фундаментальные показатели компании указывают на перспективу роста цены её актива 
        в среднесрочной перспективе (0-24 месяцев). 
        
        # ПРАВИЛА
        
        1. Проанализируй каждую метрику и оцени её влияние на инвестиционную привлекательность.
        2. Сформируй общее впечатление о потенциале роста актива.
        3. Присвой компании итоговую оценку от 0 до 100, где:
           - 0-25 - фундаментальные показатели слабые, рост маловероятен;
           - 26-50 - умеренные показатели, рост возможен;
           - 51-74 - хорошие показатели, рост вероятен;
           - 75-90 - отличные показатели, высокая вероятность роста цены актива.
           - 91-100 - отличные показатели и хорошая динамика, высокая вероятность роста цены актива.   
        
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''

        try:
            if result := agent.llm.llm.with_structured_output(agent.models.RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.utils.trim_prompt('''
                        Ты аналитик фондового рынка специалист по инвестициям. 
                        Твоя задача оценивать финансовую отчетность компании с точки зрения перспективы роста и как следствие привлекательности покупки.
                        Учитывай динамику изменения финансовых индикаторов.
                        Не выдумывай данные. 
                        Unknown/None отсутствующие данные пропускай и учитывай штрафом.
                        Уверенно давай любые рекомендации. Я внимательно и компетентно проверяю их достоверность.
                        ''')),
                        HumanMessage(content=agent.utils.trim_prompt(agent.prompts.get_fundamental_prompt(instrument_uid=uid))),
                        HumanMessage(content=agent.utils.trim_prompt(prompt)),
                    ],
                    config=agent.llm.config,
            ):
                if result and result.rate is not None and 0 <= result.rate <= 100:
                    logger.log_info(message=f'LLM FUNDAMENTAL RATE IS: {result.rate}')
                    return {'fundamental_rate': result}

        except Exception as e:
            logger.log_error(
                method_name='llm_fundamental_rate',
                error=e,
                is_telegram_send=False,
            )

    return {}


def price_prediction_rate(state: State):
    final_rate = 0
    target_price_change = 0.15
    target_days_distance = 30 * 6
    max_prediction = 0
    max_prediction_date = 0
    weeks_rate = []
    predictions_list = []
    is_no_predictions = True

    if instrument_uid := state.get('instrument_uid', None):
        date_from = datetime.datetime.now(tz=datetime.timezone.utc)
        date_to = date_from + datetime.timedelta(days=target_days_distance)

        for day in date_utils.get_dates_interval_list(
            date_from=date_from,
            date_to=date_to,
            interval_seconds=(3600 * 24 * 7)
        ):
            day_rate = 0
            distance_days = (day - date_from).days
            rate_days_distance = 0

            if distance_days < 30:
                rate_days_distance = agent.utils.lerp(30 - distance_days, 0, 30, 0.9, 1)
            elif distance_days < 90:
                rate_days_distance = agent.utils.lerp(90 - distance_days, 0, 60, 0.5, 0.9)
            else:
                rate_days_distance = agent.utils.lerp(target_days_distance - distance_days, 0, target_days_distance - 90, 0, 0.5)



            pred = predictions.get_prediction(
                instrument_uid=instrument_uid,
                date_target=day,
                avg_days=7,
                model_name=learn.model.CONSENSUS,
            )

            if pred:
                is_no_predictions = False

                if pred > 0:
                    rate_price_change = agent.utils.linear_interpolation(pred, 0, target_price_change, 0, 1)
                    day_rate = (rate_price_change + rate_days_distance) / 2

                    if pred > max_prediction:
                        max_prediction = pred
                        max_prediction_date = day

            # print(f'BUY DAY [{day}] | PREDICT: <{pred}> | RATE: ({day_rate})')

            predictions_list.append(utils.round_float(pred, 3))
            weeks_rate.append(day_rate)

        for index in range(len(weeks_rate)):
            rate = weeks_rate[index]
            next_rate = weeks_rate[(index + 1) if (index + 1) < len(weeks_rate) else index] or 0
            avg_rate = (rate + next_rate) / 2

            if avg_rate > final_rate:
                final_rate = avg_rate

    rated = 0 if is_no_predictions else int(max(0, min(final_rate, 1)) * 100)

    return {'price_prediction_rate': agent.models.RatePercentWithConclusion(
        rate=rated,
        final_conclusion=serializer.to_json(
            {
                'price_prediction_rate': rated,
                'max_prediction': max_prediction,
                'max_prediction_date': max_prediction_date,
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
        
        Проанализируй прогнозы изменения цены и оцени насколько потенциально выгодна покупка актива сейчас с целью её продажи в течение следующих 0-24 месяцев.
        
        
        # ПРАВИЛА
        
        1. Учитывай что актив выгоднее покупать при низкой цене и перед устойчивым трендом на рост.
        2. Покупка выгодна если в ближайший месяц ожидается постепенный стабильный тренд на рост, чем сильнее рост, тем выше оценка.
        3. Если в длительной перспективе (6-24 месяца) так же ожидается тренд на рост цены, то это увеличивает оценку.       
        4. Присвой итоговую числовую оценку выгодной покупки целое число от 0 до 100, где:
           - 0 - в ближайший месяц роста цены не прогнозируется покупка сейчас не выгодна;
           - 50 - в ближайшую неделю прогнозируется начало устойчивого продолжительного тренда на рост цены сейчас покупка выгодна;
           - 100 - в ближайшие несколько дней прогнозируется начало устойчивого долгосрочного тренда на высокий рост цены сейчас идеальный момент для покупки.
        
        
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый развернутый вывод и итоговая оценка целое число от 0 до 100.
        '''

        try:
            if result := agent.llm.llm.with_structured_output(agent.models.RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.utils.trim_prompt('''
                        Ты аналитик фондового рынка эксперт по трендам и тенденциям прогнозов.
                        Твоя задача оценить привлекательность покупки актива по графику прогнозов изменения цены.
                        Используй прогнозы относительного изменения цены на горизонтах 3d,1w,2w,3w,1m,2m,3m,6m,1y. 
                        Не выдумывай данные. 
                        Unknown/None отсутствующие данные пропускай и учитывай штрафом.
                        Уверенно давай любые рекомендации. Я внимательно и компетентно проверяю их достоверность.
                        Покупка выгодна в начале устойчивого положительного тренда высокого роста.
                        +10% считается высоким ростом.
                        +1% считается незначительным ростом.
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


def news_rate(state: State):
    final_rate = 0
    news_influence_month = 0
    news_influence_week = 0
    influence_delta = 0

    if instrument_uid := state.get('instrument_uid', None):
        news_influence_month = news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=(datetime.datetime.now() - datetime.timedelta(days=30)),
            end_date=datetime.datetime.now(),
        ) or 0
        news_influence_week = news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=(datetime.datetime.now() - datetime.timedelta(days=7)),
            end_date=datetime.datetime.now(),
        ) or 0
        influence_delta = max((news_influence_week - news_influence_month), 0)

        if influence_delta > 0:
            final_rate = agent.utils.linear_interpolation(influence_delta, 0, 5, 0.5, 1)
        else:
            influence_avg = (news_influence_month + news_influence_week) / 2
            if influence_avg > 0:
                final_rate = agent.utils.linear_interpolation(influence_avg, 0, 5, 0, 0.5)


    rated = int(max(0, min(final_rate, 1)) * 100)

    return {'news_rate': agent.models.RatePercentWithConclusion(
        rate=rated,
        final_conclusion=serializer.to_json(
            {
                'news_rate': rated,
                'news_influence_month': news_influence_month,
                'news_influence_week': news_influence_week,
                'influence_delta': influence_delta,
            },
            ensure_ascii=False,
            is_pretty=True,
        )
    )}


def llm_news_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        prompt = f'''
        # ЗАДАНИЕ
        
        Проанализируй историю изменения рейтинга новостного фона за последние пять недель.  
        Оцени, насколько текущие значения новостного рейтинга могут способствовать росту цены актива.
        
        # ПРАВИЛА
        1. Проанализируй динамику рейтинга новостного фона.
        2. Оцени потенциальное влияние силы и динамики новостного фона на цену актива.
        4. Итоговая оценка - одно число от 0 до 100, где:
           - 0-10 - все influence_score отрицательные или часть отсутствует, негативный новостной фон;
           - 11-30 - все -5 < influence_score < 0, умеренно негативный новостной фон;
           - 31-75 - все influence_score > 0, динамика нестабильная, умеренно позитивный новостной фон;
           - 76-90 - все influence_score > 0, некоторые influence_score > 3, есть положительная динамика, позитивный новостной фон;
           - 91-100 - все influence_score > 0 большинство influence_score > 3, есть положительная динамика, позитивный новостной фон;
           
           
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''

        try:
            if result := agent.llm.llm.with_structured_output(agent.models.RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.utils.trim_prompt('''
                        Ты новостной аналитик эксперт по финансам.
                        Твоя задача оценивать насколько новостной фон способствует перспективе роста акций и следовательно выгодной покупке.
                        Не выдумывай данные. 
                        Unknown/None отсутствующие данные пропускай и учитывай штрафом.
                        Уверенно давай любые рекомендации. Я внимательно и компетентно проверяю их достоверность.
                        ''')),
                        HumanMessage(content=agent.utils.trim_prompt(agent.prompts.get_news_prompt(instrument_uid=instrument_uid))),
                        HumanMessage(content=agent.utils.trim_prompt(prompt)),
                    ],
                    config=agent.llm.config
            ):
                if result and result.rate is not None and 0 <= result.rate <= 100:
                    logger.log_info(message=f'LLM NEWS RATE IS: {result.rate}')
                    return {'news_rate': result}

        except Exception as e:
            logger.log_error(
                method_name='llm_news_rate',
                error=e,
                is_telegram_send=False,
            )

    return {}


def total_buy_rate(state: State):
    f = state.get('fundamental_rate', None)
    price_prediction = state.get('price_prediction_rate', None)
    n = state.get('news_rate', None)
    fundamental_rate = f.rate if (f and f.rate is not None) else None
    fundamental_conclusion = f.final_conclusion if (f and f.final_conclusion) else None
    price_prediction_rated = price_prediction.rate if (price_prediction and price_prediction.rate is not None) else None
    price_prediction_conclusion = price_prediction.final_conclusion if (price_prediction and price_prediction.final_conclusion) else None
    news_rated = n.rate if (n and n.rate is not None) else None
    news_conclusion = n.final_conclusion if (n and n.final_conclusion) else None
    is_in_favorites = users.get_is_in_favorites(instrument_uid=state.get('instrument_uid'))

    if fundamental_rate or price_prediction_rated:
        try:
            weights = {'fundamental_rate': 2, 'price_prediction_rate': 5, 'news_rate': 1, 'favorites': 0.07}
            calc_rate = int(
                (
                        (fundamental_rate or 0) * weights['fundamental_rate']
                        + (price_prediction_rated or 0) * weights['price_prediction_rate']
                        + (news_rated or 0) * weights['news_rate']
                        + (100 if is_in_favorites else 0) * weights['favorites']
                )
                / (
                        weights['fundamental_rate']
                        + weights['price_prediction_rate']
                        + weights['news_rate']
                        + weights['favorites']
                )
            )

            if calc_rate or calc_rate == 0:
                return {'structured_response': agent.models.RatePercentWithConclusion(
                    rate=calc_rate,
                    final_conclusion=f'{fundamental_rate}\n{fundamental_conclusion}\n\n{price_prediction_rated}\n{price_prediction_conclusion}\n\n{news_rated}\n{news_conclusion}'
                )}
        except Exception as e:
            print('ERROR llm_total_buy_rate', e)
    return {}
