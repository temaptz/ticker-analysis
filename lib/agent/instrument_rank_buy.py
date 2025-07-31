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
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils, db_2, logger, forecasts
from lib.agent import models, llm, planner


class RatePercent(BaseModel):
    rate: int

class State(TypedDict, total=False):
    instrument_uid: str
    fundamental_rate: int
    price_prediction_rate: int
    news_rate: int
    comment_fundamental: str
    comment_price_prediction: str
    structured_response: int


def update_recommendations():
    graph_buy = get_buy_rank_graph()

    for i in users.sort_instruments_for_buy(
            instruments_list=instruments.get_instruments_white_list()
    ):
        if not i.for_qual_investor_flag:
            try:
                result = graph_buy.invoke(
                    input={'instrument_uid': i.uid},
                    debug=True,
                    config=llm.config,
                )

                if rate := result.get('structured_response', None):
                    db_2.instrument_tags_db.upset_tag(
                        instrument_uid=i.uid,
                        tag_name='llm_buy_rate',
                        tag_value=rate,
                    )

                    logger.log_info(
                        message=f'Сохранена оценка покупки {i.name}\nОценка: {rate}',
                        is_send_telegram=True,
                    )
            except Exception as e:
                logger.log_error(method_name='update_recommendations_item buy', error=e)


def get_buy_rank_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(State)

    graph_builder.add_node('llm_fundamental_rate', llm_fundamental_rate)
    graph_builder.add_node('llm_price_prediction_rate', llm_price_prediction_rate)
    graph_builder.add_node('llm_news_rate', llm_news_rate)
    graph_builder.add_node('llm_comment_fundamental', llm_comment_fundamental)
    graph_builder.add_node('llm_comment_price_prediction', llm_comment_price_prediction)
    graph_builder.add_node('llm_total_buy_rate', llm_total_buy_rate)

    graph_builder.add_edge(START, 'llm_fundamental_rate')
    graph_builder.add_edge('llm_fundamental_rate', 'llm_price_prediction_rate')
    graph_builder.add_edge('llm_price_prediction_rate', 'llm_news_rate')
    graph_builder.add_edge('llm_news_rate', 'llm_comment_fundamental')
    graph_builder.add_edge('llm_comment_fundamental', 'llm_comment_price_prediction')
    graph_builder.add_edge('llm_comment_price_prediction', 'llm_total_buy_rate')
    graph_builder.add_edge('llm_total_buy_rate', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='buy_rank_graph',
    )

    return graph


def llm_fundamental_rate(state: State):
    if uid := state.get('instrument_uid', None):
        fundamental_message = HumanMessage(content=agent.prompts.get_fundamental_prompt(instrument_uid=uid))
        human_message = HumanMessage(content=f'''
        # ЗАДАНИЕ
        
        Как специалист по инвестициям проанализируй фундаментальные показатели компании и дай оценку от 0 до 100, 
        насколько фундаментальные показатели компании указывают на перспективу роста цены её акций 
        в среднесрочной перспективе (0-24 месяцев). 
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй каждую метрику и оцени её влияние на инвестиционную привлекательность.
        2. Сформируй общее впечатление о потенциале роста акций.
        3. Присвой компании итоговую **оценку от 0 до 100**, где:
           - 0-25 - фундаментальные показатели слабые, рост маловероятен;
           - 26-50 - умеренные показатели, потенциал роста неочевиден;
           - 51-75 - сильные показатели, умеренно высокий потенциал роста;
           - 76-100 - отличные показатели, высокая вероятность роста цены акций.
        4. В ответе должно быть только число от 0 до 100.
        ''')


        print('HUMAN MESSAGE fundamental_rate', human_message.content)

        try:
            if result := llm.llm.with_structured_output(RatePercent).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        fundamental_message,
                        human_message,
                    ],
                    config=llm.config
            ):
                if (rate := result.rate) is not None:
                    logger.log_info(message=f'LLM FUNDAMENTAL RATE IS: {rate}')
                    return {'fundamental_rate': rate}

        except Exception as e:
            logger.log_error(
                method_name='llm_fundamental_rate',
                error=e,
                is_telegram_send=False,
            )

    return {}


def llm_price_prediction_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        price_message = HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid))
        human_message = HumanMessage(content=f'''
        # ЗАДАНИЕ
        
        Как специалист по трейдингу проанализируй текущую цену акции и прогноз относительного изменения цены. 
        Оцени, насколько выгодна покупка акции сейчас с целью её продажи в течение следующих 0-24 месяцев.
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй изменение цены на каждом интервале времени.
        2. Оцени стабильность и направление ожидаемой динамики.
        3. На основе анализа, прими решение о привлекательности покупки.
        4. Присвой итоговую числовую оценку от 0 до 100, где:
           - 0-25 - рост стабильно отрицательный, покупка убыточна;
           - 26-50 - рост маловероятен, покупка мало привлекательна;
           - 51-75 - умеренный потенциал роста и выгоды;
           - 76-100 - высокий потенциал роста и выгоды.
        
        # ФОРМАТ ОТВЕТА
        
        Выведи только одно целое число от 0 до 100. Не добавляй объяснений.
        ''')


        print('HUMAN MESSAGE price_prediction', human_message.content)

        try:
            if result := llm.llm.with_structured_output(RatePercent).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        price_message,
                        human_message,
                    ],
                    config=llm.config,
            ):
                if (rate := result.rate) is not None:
                    logger.log_info(message=f'LLM PRICE PREDICTION RATE IS: {rate}')
                    return {'price_prediction_rate': rate}

        except Exception as e:
            logger.log_error(
                method_name='llm_price_prediction_rate',
                error=e,
                is_telegram_send=False,
            )

    return {}


def llm_news_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        human_message = HumanMessage(content=f'''
        # ЗАДАНИЕ
        
        Как специалист по медиа проанализируй рейтинг новостного фона за указанные периоды.  
        Оцени, насколько текущие значения новостного рейтинга могут способствовать росту цены акции в течение следующих 0-24 месяцев.
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй динамику рейтинга новостного фона по периодам.
        2. Оцени силу и стабильность позитивного влияния новостей на цену акции.
        3. На основе анализа присвой итоговую оценку инвестиционной привлекательности.
        4. Итог — одно число от 0 до 100, где:
           - 0-25 - негативная динамика новостного фона;
           - 26-50 - умеренно негативная динамика новостного фона;
           - 51-75 - умеренно позитивная динамика новостного фона;
           - 76-100 - стабильно позитивная динамика новостного фона.;
        5. Снижай оценку при нулевом или отсутствующем новостном фоне. Если данные полностью отсутствуют, оценка 0.
           
        # ФОРМАТ ОТВЕТА
        
        Ответ — **только одно целое число от 0 до 100**. Без объяснений.
        ''')


        print('HUMAN MESSAGE news_rate', human_message.content)

        try:
            if result := llm.llm.with_structured_output(RatePercent).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        HumanMessage(content=agent.prompts.get_news_prompt(instrument_uid=instrument_uid)),
                        human_message,
                    ],
                    config=llm.config
            ):
                if (rate := result.rate) is not None:
                    logger.log_info(message=f'LLM NEWS RATE IS: {rate}')
                    return {'news_rate': rate}

        except Exception as e:
            logger.log_error(
                method_name='llm_news_rate',
                error=e,
                is_telegram_send=False,
            )

    return {}


def llm_comment_fundamental(state: State):
    if uid := state.get('instrument_uid', None):
        fundamental_message = HumanMessage(content=agent.prompts.get_fundamental_prompt(instrument_uid=uid))
        human_message = HumanMessage(content=f'''
        # ЗАДАНИЕ
        
        Как финансовый консультант проанализируй фундаментальные показатели компании.  
        Оцени их с точки зрения потенциала роста ее акций. 
        В ответе должен быть только окончательный вывод.
        ''')


        print('HUMAN MESSAGE comment_fundamental', human_message.content)

        try:
            if result := llm.llm.invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        SystemMessage(content=agent.prompts.get_thinking_prompt()),
                        fundamental_message,
                        human_message,
                    ],
                    config=llm.config
            ):
                if rate := result.content:
                    logger.log_info(message=f'LLM COMMENT FUNDAMENTAL IS: {rate}')
                    return {'comment_fundamental': rate}

        except Exception as e:
            logger.log_error(
                method_name='llm_comment_fundamental',
                error=e,
                is_telegram_send=False,
            )

    return {}


def llm_comment_price_prediction(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        human_message = HumanMessage(content=f'''
        # ЗАДАНИЕ
                
        Как финансовый консультант проанализируй текущую цену акции и прогноз относительного изменения цены. 
        Оцени, насколько выгодна покупка акции сейчас с целью её продажи в течение следующих 0-24 месяцев. 
        В ответе должен быть только окончательный вывод.
        ''')


        print('HUMAN MESSAGE comment_price_prediction', human_message.content)

        try:
            if result := llm.llm.invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        SystemMessage(content=agent.prompts.get_thinking_prompt()),
                        HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid)),
                        human_message,
                    ],
                    config=llm.config
            ):
                if comment := result.content:
                    logger.log_info(message=f'LLM COMMENT PRICE PREDICTION IS: {comment}')
                    return {'comment_price_prediction': comment}

        except Exception as e:
            logger.log_error(
                method_name='llm_comment_price_prediction',
                error=e,
                is_telegram_send=False,
            )

    return {}


def llm_total_buy_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        fundamental_rate = state.get('fundamental_rate', 'Unknown')
        price_prediction_rate = state.get('price_prediction_rate', 'Unknown')
        news_rate = state.get('news_rate', 'Unknown')
        comment_fundamental = state.get('comment_fundamental', 'Unknown')
        comment_price_prediction = state.get('comment_price_prediction', 'Unknown')

        if fundamental_rate or price_prediction_rate or news_rate:
            human_message = HumanMessage(content=f'''
            # ОЦЕНКИ ИНВЕСТИЦИОННОЙ ПРИВЛЕКАТЕЛЬНОСТИ

            1. Прогноз изменения цены - price_prediction_rate: {price_prediction_rate} (0-100) #Самый важный
            2. Фундаментальные показатели - fundamental_rate: {fundamental_rate} (0-100) #Второй по значимости
            3. Новостной фон - news_rate: {news_rate} (0-100) #Может быть не точным, должен учитываться третьим по значению 
            
            # КОММЕНТАРИЙ О ФУНДАМЕНТАЛЬНЫХ ПОКАЗАТЕЛЯХ
            {comment_fundamental}
            
            # КОММЕНТАРИЙ О ПРОГНОЗЕ ИЗМЕНЕНИЯ ЦЕНЫ
            {comment_price_prediction}
            
            # ЗАДАНИЕ
            
            Как специалист по биржевой торговле оцени насколько выгодна покупка этого инструмента именно сейчас с целью последующей продажи.

            # ИНСТРУКЦИЯ
            
            1. Используй оценки инвестиционной привлекательности, которые были выражены числом от 0 до 100.
            2. Самый главный показатель на который надо опираться в ответе - оценка прогноза изменения цены price_prediction_rate.
            3. Второй по значимости показатель - прогноз относительного изменения цены price_prediction.
            4. Второй по значимости показатель - фундаментальные показатели fundamental_rate.
            5. Третий по значимости показатель - новостной фон news_rate, он может быть не точным, но все равно учитывай его.
            6. Присвой итоговую оценку от 0 до 100, где:
               - 0 - покупка нецелесообразна;
               - 100 - максимально выгодный момент для покупки.
            7. Эта оценка будет использоваться для сравнения между инструментами.
            8. Высокая итоговая оценка возможна только если есть все данные и все оценки высоки.
            9. Если нет прогнозов цен, то то итоговая оценка должна быть низкой или нулевой.
            10. Учитывай комментарии о фундаментальных показателях и прогнозе изменения цены в них содержатся важные выводы которые следует учесть.
            11. Учитывай всю собранную ранее информацию.
            
            # ФОРМАТ ОТВЕТА
            
            Ответ - **только одно целое число от 0 до 100**. Без пояснений.
            ''')


            print('HUMAN MESSAGE total_buy_rate', human_message.content)

            try:
                if result := llm.llm.with_structured_output(RatePercent).invoke(
                        [
                            SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                            SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                            SystemMessage(content=agent.prompts.get_thinking_prompt()),
                            HumanMessage(content=agent.prompts.get_instrument_info_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=agent.prompts.get_fundamental_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid)),
                            human_message
                        ],
                        config=llm.config
                ):
                    if (rate := result.rate) is not None:
                        logger.log_info(message=f'LLM TOTAL BUY RATE IS: {rate}')
                        return {'structured_response': rate}

            except Exception as e:
                logger.log_error(
                    method_name='llm_total_buy_rate',
                    error=e,
                    is_telegram_send=False,
                )
    return {}
