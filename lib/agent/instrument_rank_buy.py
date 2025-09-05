import os
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils, db_2, logger, forecasts
from lib.agent import llm


class RatePercentWithConclusion(BaseModel):
    rate: int
    final_conclusion: str

class State(TypedDict, total=False):
    human_name: str
    instrument_uid: str
    fundamental_rate: RatePercentWithConclusion
    price_prediction_rate: RatePercentWithConclusion
    news_rate: RatePercentWithConclusion
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
                    config=llm.config,
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
                            message=f'Сохранена оценка покупки {i.name}\nОценка: {structured_response.rate}\nКомментарий: {structured_response.final_conclusion}\nПрошлая оценка: {previous_rate}',
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
    graph_builder.add_node('llm_price_prediction_rate', llm_price_prediction_rate)
    graph_builder.add_node('llm_news_rate', llm_news_rate)
    graph_builder.add_node('llm_total_buy_rate', llm_total_buy_rate)

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
        
        Как специалист по инвестициям проанализируй фундаментальные показатели компании и дай оценку от 0 до 100, 
        насколько фундаментальные показатели компании указывают на перспективу роста цены её актива 
        в среднесрочной перспективе (0-24 месяцев). 
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй каждую метрику и оцени её влияние на инвестиционную привлекательность.
        2. Сформируй общее впечатление о потенциале роста актива.
        3. Присвой компании итоговую оценку от 0 до 100, где:
           - 0-25 - фундаментальные показатели слабые, рост маловероятен;
           - 26-50 - умеренные показатели, рост возможен;
           - 51-74 - хорошие показатели, рост вероятен;
           - 75-90 - отличные показатели, высокая вероятность роста цены актива.
           - 91-100 - отличные показатели и хорошая динамика, высокая вероятность роста цены актива.   
        4. На основе шкалы данной инструкции построй собственную более развернутую шкалу и дай по ней окончательную точную оценку.
        
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''


        print('HUMAN MESSAGE fundamental_rate', prompt)

        try:
            if result := llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        SystemMessage(content=agent.prompts.get_thinking_prompt()),
                        HumanMessage(content=agent.prompts.get_fundamental_prompt(instrument_uid=uid)),
                        HumanMessage(content=prompt),
                    ],
                    config=llm.config
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


def llm_price_prediction_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        prompt = f'''
        # ЗАДАНИЕ
        
        Как специалист по трейдингу проанализируй и оцени насколько выгодна покупка актива сейчас с целью её продажи в течение следующих 0-24 месяцев.
        
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй прогноз изменения цены price_prediction на каждом интервале времени, оцени стабильность и направление ожидаемой динамики.
        2. Учитывай что актив выгоднее покупать при низкой цене и перед устойчивым трендом на рост.
        3. Оцени, насколько выгодна покупка актива именно сейчас.
        4. Покупка выгодна если в ближайший месяц ожидается постепенный стабильный тренд на рост, чем сильнее рост, тем выше оценка.
        5. Если в длительной перспективе (6-24 месяца) так же ожидается тренд на рост цены, то это увеличивает оценку.       
        6. Незначительное снижение в течении нескольких дней перед стабильным ростом говорит о хорошем моменте для покупки и увеличивает оценку.
        7. Присвой итоговую числовую оценку выгодной покупки целое число от 0 до 100, где:
           - 0 - все price_prediction на ближайший месяц и меньше стабильно отрицательные, покупка в ближайшее время не выгодна;
           - 1-49 - в ближайший месяц и меньше присутствуют отрицательные price_prediction, покупка не рекомендована;
           - 50-74 - все price_prediction до месяца стабильно положительные, покупка возможна;
           - 75-89 - все price_prediction до трех месяцев стабильно положительные, сейчас хороший момент для покупки.
           - 90-100 - все price_prediction до пол года стабильно положительные, сейчас идеальный момент для покупки.
        8. На основе шкалы данной инструкции построй собственную более развернутую шкалу и дай по ней окончательную точную оценку.
        9. В конце кратко обобщи все рассуждение сформулируй итоговый вывод и итоговую оценку целое число от 0 до 100.
        
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''


        print('HUMAN MESSAGE price_prediction', prompt)

        try:
            if result := llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        SystemMessage(content=agent.prompts.get_thinking_prompt()),
                        HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid)),
                        HumanMessage(content=prompt),
                    ],
                    config=llm.config,
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


def llm_news_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        prompt = f'''
        # ЗАДАНИЕ
        
        Как специалист по медиа проанализируй рейтинг новостного фона за указанные периоды.  
        Оцени, насколько текущие значения новостного рейтинга могут способствовать росту цены актива.
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй динамику рейтинга новостного фона по периодам.
        2. Оцени силу и стабильность позитивного влияния новостей на цену актива.
        4. Итоговая оценка - одно число от 0 до 100, где:
           - 0-10 - все influence_score отрицательные или часть отсутствует, негативный новостной фон;
           - 11-30 - все -5 < influence_score < 0, умеренно негативный новостной фон;
           - 31-75 - все influence_score > 0, динамика нестабильная, умеренно позитивный новостной фон;
           - 76-90 - все influence_score > 0, некоторые influence_score > 3, есть положительная динамика, позитивный новостной фон;
           - 91-100 - все influence_score > 0 большинство influence_score > 3, есть положительная динамика, позитивный новостной фон;
        5. Снижай оценку при нулевом или отсутствующем новостном фоне. Если данные полностью отсутствуют, оценка 0.
        6. На основе шкалы данной инструкции построй собственную более развернутую шкалу и дай по ней окончательную точную оценку.
           
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''


        print('HUMAN MESSAGE news_rate', prompt)

        try:
            if result := llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_thinking_prompt()),
                        HumanMessage(content=agent.prompts.get_news_prompt(instrument_uid=instrument_uid)),
                        HumanMessage(content=prompt),
                    ],
                    config=llm.config
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


def llm_total_buy_rate(state: State):
    f = state.get('fundamental_rate', None)
    price_prediction = state.get('price_prediction_rate', None)
    n = state.get('news_rate', None)
    fundamental_rate = f.rate if (f and f.rate) else None
    fundamental_conclusion = f.final_conclusion if (f and f.final_conclusion) else None
    price_prediction_rate = price_prediction.rate if (price_prediction and price_prediction.rate) else None
    price_prediction_conclusion = price_prediction.final_conclusion if (price_prediction and price_prediction.final_conclusion) else None
    news_rate = n.rate if (n and n.rate) else None
    news_conclusion = n.final_conclusion if (n and n.final_conclusion) else None
    is_in_favorites = users.get_is_in_favorites(instrument_uid=state.get('instrument_uid'))

    if fundamental_rate or price_prediction_rate:
        try:
            weights = {'fundamental_rate': 1, 'price_prediction_rate': 2, 'news_rate': 1, 'favorites': 0.05}
            calc_rate = int(
                (
                        (fundamental_rate or 0) * weights['fundamental_rate']
                        + (price_prediction_rate or 0) * weights['price_prediction_rate']
                        + (news_rate or 0) * weights['news_rate']
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
                return {'structured_response': RatePercentWithConclusion(
                    rate=calc_rate,
                    final_conclusion=f'{fundamental_conclusion}\n{price_prediction_conclusion}\n{news_conclusion}'
                )}
        except Exception as e:
            print('ERROR llm_total_buy_rate', e)
    return {}
