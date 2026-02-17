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
    macd_buy_rate: agent.models.RatePercentWithConclusion
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
    graph_builder.add_node('price_prediction_rate', price_prediction_rate)
    graph_builder.add_node('news_rate', news_rate)
    graph_builder.add_node('macd_buy_rate', macd_buy_rate)
    graph_builder.add_node('total_buy_rate', total_buy_rate)

    graph_builder.add_edge(START, 'llm_fundamental_rate')
    graph_builder.add_edge('llm_fundamental_rate', 'price_prediction_rate')
    graph_builder.add_edge('price_prediction_rate', 'news_rate')
    graph_builder.add_edge('news_rate', 'macd_buy_rate')
    graph_builder.add_edge('macd_buy_rate', 'total_buy_rate')
    graph_builder.add_edge('total_buy_rate', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='buy_rank_graph',
    )

    return graph


def llm_fundamental_rate(state: State):
    if uid := state.get('instrument_uid', None):
        db_rate = db_2.instrument_tags_db.get_tag(instrument_uid=uid, tag_name='llm_fundamental_rate')
        db_conclusion = db_2.instrument_tags_db.get_tag(instrument_uid=uid, tag_name='llm_fundamental_conclusion')

        # Данные будут обновляться при отсутствии или в первый понедельник месяца. В остальные дни кэш
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        is_first_monday = ((now.weekday() == 0) and (1 <= now.day <= 7))
        if not is_first_monday and db_rate is not None and db_rate.tag_value is not None:
            return {'fundamental_rate': agent.models.RatePercentWithConclusion(
                rate=int(db_rate.tag_value),
                final_conclusion=str(db_conclusion.tag_value)
            )}

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
                    db_2.instrument_tags_db.upset_tag(instrument_uid=uid, tag_name='llm_fundamental_rate', tag_value=result.rate)
                    db_2.instrument_tags_db.upset_tag(instrument_uid=uid, tag_name='llm_fundamental_conclusion', tag_value=result.final_conclusion)
                    return {'fundamental_rate': result}

        except Exception as e:
            logger.log_error(
                method_name='llm_fundamental_rate',
                error=e,
                is_telegram_send=False,
            )

    return {}


def price_prediction_rate(state: State):
    rate = {}

    if instrument_uid := state.get('instrument_uid', None):
        rate = agent.price.price_buy_rate(instrument_uid=instrument_uid)

    return {'price_prediction_rate': agent.models.RatePercentWithConclusion(
        rate=rate.get('rate', 0),
        final_conclusion=serializer.to_json(
            {
                'max_prediction_value': rate.get('max_prediction_value', 0),
                'max_prediction_date': rate.get('max_prediction_date', 0),
                'predictions': '; '.join(map(str, rate.get('predictions', []))),
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

        if news_influence_month > 0:
            if news_influence_week > news_influence_month:
                final_rate = 100
            else :
                final_rate = 50
        else:
            final_rate = 0

    return {'news_rate': agent.models.RatePercentWithConclusion(
        rate=final_rate,
        final_conclusion=serializer.to_json(
            {
                'final_rate': final_rate,
                'news_influence_month': news_influence_month,
                'news_influence_week': news_influence_week,
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


def macd_buy_rate(state: State):
    final_rate = 0
    graph_hist = []

    if instrument_uid := state.get('instrument_uid', None):
        if rated := agent.macd.macd_buy_rate(instrument_uid=instrument_uid):
            if rated['rate'] is not None:
                final_rate = rated['rate']
                graph_hist = rated['graph_hist'] or []


    return {'macd_buy_rate': agent.models.RatePercentWithConclusion(
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


def total_buy_rate(state: State):
    result = agent.buy_sell_rate.get_total_buy_rate(instrument_uid=state.get('instrument_uid'))

    if result and (result.get('rate') or result.get('rate') == 0):
        return {'structured_response': agent.models.RatePercentWithConclusion(
            rate=result['rate'] * 100,
            final_conclusion=result['conclusion']
        )}
    return {}
