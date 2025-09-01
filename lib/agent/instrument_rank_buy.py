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
    logger.log_info(
        message='LANGSMITH DEBUG RECOMMENDATIONS BUY',
        output={
            'LANGSMITH_TRACING': os.environ['LANGSMITH_TRACING'],
            'LANGSMITH_ENDPOINT': os.environ['LANGSMITH_ENDPOINT'],
            'LANGSMITH_API_KEY': os.environ['LANGSMITH_API_KEY'],
            'LANGSMITH_PROJECT': os.environ['LANGSMITH_PROJECT'],
        },
        is_send_telegram=True,
    )

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
                if result and result.rate is not None:
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
        
        1. Проанализируй прогноз изменения цены на каждом интервале времени.
        2. Оцени стабильность и направление ожидаемой динамики.
        3. На основе анализа, прими решение о привлекательности покупки.
        4. Учти что актив выгоднее покупать по низкой цене перед трендом на рост в ближайший месяц.
        5. Чем выше тренд на рост, тем выше должна быть твоя оценка.
        6. Присвой итоговую числовую оценку выгодности покупки от 0 до 100, где:
           - 0-25 - прогноз цены стабильно отрицательный, покупка убыточна;
           - 26-50 - в ближайший месяц прогнозируется незначительный рост, покупка мало привлекательна;
           - 51-75 - прогноз цены в ближайший месяц стабильно положительный, покупка привлекательна;
           - 76-100 - в ближайшее время больше месяца прогнозируется высокий рост, покупка максимально привлекательна.
        7. Если в ближайшие несколько месяцев прогнозируется стабильный высокий рост, а в ближайшие пару недель прогнозируется небольшое краткосрочное снижение, то оценивай рост в перспективе как более важный и считай покупку на падении привлекательной и выгодной.
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
                        HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid, is_for_sell=False)),
                        HumanMessage(content=prompt),
                    ],
                    config=llm.config,
            ):
                if result and result.rate is not None:
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
           - 0-25 - негативный рейтинг новостного фона;
           - 26-50 - умеренно негативная динамика новостного фона;
           - 51-75 - умеренно позитивная динамика новостного фона;
           - 76-90 - стабильно позитивный новостной фон;
           - 91-100 - положительная динамика позитивного новостного фона;
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
                        HumanMessage(content=agent.prompts.get_news_prompt(instrument_uid=instrument_uid, is_for_sell=False)),
                        HumanMessage(content=prompt),
                    ],
                    config=llm.config
            ):
                if result and result.rate is not None:
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
    if instrument_uid := state.get('instrument_uid', None):
        f = state.get('fundamental_rate', None)
        price_prediction = state.get('price_prediction_rate', None)
        n = state.get('news_rate', None)
        fundamental_rate = f.rate if (f and f.rate) else None
        fundamental_conclusion = f.final_conclusion if (f and f.final_conclusion) else None
        price_prediction_rate = price_prediction.rate if (price_prediction and price_prediction.rate) else None
        price_prediction_conclusion = price_prediction.final_conclusion if (price_prediction and price_prediction.final_conclusion) else None
        news_rate = n.rate if (n and n.rate) else None
        news_conclusion = n.final_conclusion if (n and n.final_conclusion) else None

        if fundamental_rate or price_prediction_rate or news_rate:
            human_message = HumanMessage(content=f'''
            # ПРЕДВАРИТЕЛЬНЫЕ ОЦЕНКИ

            1. Прогноз изменения цены - price_prediction_rate: {price_prediction_rate} [0-100] #Самый важный
            2. Фундаментальные показатели - fundamental_rate: {fundamental_rate} [0-100] #Второй по значимости
            3. Новостной фон - news_rate: {news_rate} [0-100] #Второй по значимости 
            
            # КОММЕНТАРИЙ О ФУНДАМЕНТАЛЬНЫХ ПОКАЗАТЕЛЯХ
            {fundamental_conclusion}
            
            # КОММЕНТАРИЙ О ПРОГНОЗЕ ИЗМЕНЕНИЯ ЦЕНЫ
            {price_prediction_conclusion}
            
            # КОММЕНТАРИЙ О НОВОСТНОМ ФОНЕ
            {news_conclusion}
            
            # АКТИВ В ИЗБРАННОМ
            is_in_favorites: {'True' if users.get_is_in_favorites(instrument_uid=instrument_uid) else 'False'}
            
            # ЗАДАНИЕ
            
            Как специалист по биржевой торговле проанализируй все показатели и оцени насколько выгодна покупка этого актива именно сейчас с целью последующей продажи. Для оценки составь сложную независимую шкалу на основе инструкции.

            # ИНСТРУКЦИЯ
            
            1. Используй предварительные оценки, которые выражены числом от 0 до 100.
            2. Самый главный показатель на который надо опираться в ответе - оценка прогноза изменения цены price_prediction_rate.
            3. Второй по значимости показатель - фундаментальные показатели fundamental_rate.
            4. Второй по значимости показатель - новостной фон news_rate, он может быть не точным.
            5. Важный показатель - прогноз относительного изменения цены price_prediction, нужно его учитывать.
            6. Присвой итоговую оценку от 0 до 100, где:
               - 0-25 - оценки низкие, покупка нецелесообразна;
               - 26-50 - оценки ниже среднего, покупка рискованна;
               - 51-75 - оценки выше среднего, момент для выгодной покупки;
               - 76-100 - все оценки высоки, это максимально выгодный момент для покупки актива.
            7. Эта оценка будет использоваться для сравнения между активами.
            8. Высокая итоговая оценка возможна только если есть все данные и все оценки высоки.
            9. Если нет прогнозов цен, то то итоговая оценка должна быть низкой или нулевой.
            10. Если инструмент в избранном, то это должно давать +5% к итоговой оценке, при условии что оценка выше среднего.
            11. Учитывай комментарии, в них содержатся важные выводы которые следует учесть.
            12. Учитывай всю собранную ранее информацию.
            13. На основе шкалы данной инструкции построй собственную более развернутую шкалу и дай по ней окончательную точную оценку.
            
            # ФОРМАТ ОТВЕТА
        
            Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
            ''')


            print('HUMAN MESSAGE total_buy_rate', human_message.content)

            try:
                if result := llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                        [
                            SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                            SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                            SystemMessage(content=agent.prompts.get_thinking_prompt()),
                            HumanMessage(content=agent.prompts.get_instrument_info_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=agent.prompts.get_fundamental_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid, is_for_sell=False)),
                            human_message
                        ],
                        config=llm.config
                ):
                    if result and result.rate is not None:
                        logger.log_info(message=f'LLM TOTAL BUY RATE IS: {result.rate}')
                        return {'structured_response': result}

            except Exception as e:
                logger.log_error(
                    method_name='llm_total_buy_rate',
                    error=e,
                    is_telegram_send=False,
                )
    return {}
