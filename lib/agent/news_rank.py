import os
import time
from typing import TypedDict
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel
from lib import instruments, news, db_2, logger, types_util, users
from lib.agent import llm


class Value(BaseModel):
    value: float

class State(TypedDict, total=False):
    human_name: str
    news_text: str
    sentiment: float
    impact_strength: float
    mention_focus: float
    structured_response: types_util.NewsRate2


def rank_last_news():
    logger.log_info(
        message='LANGSMITH DEBUG NEWS RANKING',
        output={
            'LANGSMITH_TRACING': os.getenv('LANGSMITH_TRACING'),
            'LANGSMITH_ENDPOINT': os.getenv('LANGSMITH_ENDPOINT'),
            'LANGSMITH_API_KEY': os.getenv('LANGSMITH_API_KEY'),
            'LANGSMITH_PROJECT': os.getenv('LANGSMITH_PROJECT'),
        },
        is_send_telegram=True,
    )
    graph = get_news_rank_graph()

    for i in users.sort_instruments_cost(
            instruments_list=instruments.get_instruments_white_list()
    ):
        try:
            if human_name := instruments.get_instrument_human_name(uid=i.uid):
                if n := news.news.get_last_unrated_news_by_instrument_uid(instrument_uid=i.uid):
                    graph_input: State = {
                        'human_name': human_name,
                        'news_text': f'Заголовок:\n{n.title}\n\nТекст:\n{n.text}',
                    }
                    print('BEFORE GRAPH RUN', human_name)
                    start = time.time()
                    result = graph.invoke(
                        input=graph_input,
                        debug=True,
                        config=llm.config,
                    )
                    end = time.time()

                    print('NEWS RATE GRAPH RESULT', result)


                    if structured_response := result.get('structured_response', None):
                        sentiment = structured_response.get('sentiment', None)
                        impact_strength = structured_response.get('impact_strength', None)
                        mention_focus = structured_response.get('mention_focus', None)

                        if sentiment is not None and impact_strength is not None and mention_focus is not None:
                            if n_rate := types_util.NewsRate2(
                                sentiment=sentiment,
                                impact_strength=impact_strength,
                                mention_focus=mention_focus,
                            ):
                                db_2.news_rate_2_db.insert_or_update_rate(
                                    news_uid=n.news_uid,
                                    instrument_uid=i.uid,
                                    news_rate=n_rate,
                                    model_name=llm.model_name,
                                    generation_time_sec=(end - start),
                                )

                                logger.log_info(message=f'RANKED NEWS for {human_name}. NEWS DATE: {n.date}', is_send_telegram=False)

                            # logger.log_info(
                            #     message=f'Оценена новость для:\n{human_name}\nЗаголовок: {n.title}\nОценка: {serializer.to_json(n_rate)}',
                            #     is_send_telegram=True,
                            # )
        except Exception as e:
            logger.log_error(method_name='rank_last_news_item', error=e)


def get_news_rank_graph() -> CompiledStateGraph:
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(State)

    graph_builder.add_node('sentiment_rate', sentiment_rate)
    graph_builder.add_node('impact_strength_rate', impact_strength_rate)
    graph_builder.add_node('mention_focus_rate', mention_focus_rate)
    graph_builder.add_node('llm_total_result', llm_total_result)

    graph_builder.add_edge(START, 'sentiment_rate')
    graph_builder.add_edge('sentiment_rate', 'impact_strength_rate')
    graph_builder.add_edge('impact_strength_rate', 'mention_focus_rate')
    graph_builder.add_edge('mention_focus_rate', 'llm_total_result')
    graph_builder.add_edge('llm_total_result', END)

    graph = graph_builder.compile(
        checkpointer=checkpointer,
        debug=True,
        name='news_rank_graph',
    )

    return graph


main_news_prompt = f'''
Ты - специалист по анализу новостей. 
Я передаю тебе критерий оценки, название организации, текст новости.
Ты однозначно и точно оцениваешь события описанные в данной новости по данному критерию в отношении данной организации.
Для заданного критерия оценивай новость не в целом, а именно по отношению к организации.
Общий смысл новости может отличаться от контекста упоминания организации.
При подготовке ответа используй метод Tree of Thoughts.
'''


def sentiment_rate(state: State):
    if human_name := state.get('human_name', None):
        if news_text := state.get('news_text', None):
            try:
                prompt = f'''
                # КРИТЕРИЙ ОЦЕНКИ
                sentiment - Тон новости относительно организации, насколько событие описываемое в новости положительно или отрицательно по отношению к организации.
                Измеряется в диапазоне от -1.00 до 1.00, где:
                -1.00 - крайне негативный тон. Прямые обвинения в мошенничестве, банкротство, уголовное преследование, санкции;
                -0.75 - очень негативный тон. Новости о крупных финансовых потерях, уход ключевых фигур, массовые увольнения;
                -0.50 - негативный тон. Понижение кредитного рейтинга, забастовки, судебные иски;
                -0.25 - умеренно негативный тон. Критика продуктов, невыполнение планов, негативные прогнозы аналитиков;
                0.00 - нейтральный тон. Объективная информация, статистика, отчеты без эмоциональной окраски;
                0.25 - умеренно позитивный тон. Новые партнерства, запуск новых продуктов, позитивные прогнозы аналитиков;
                0.50 - позитивный тон. Рост прибыли, перевыполнение планов, получение наград;
                0.75 - очень позитивный тон. Крупные контракты, выход на новые рынки, M&A;
                1.00 - крайне позитивный тон. Революционные технологии, одобрение регуляторов, рекордная прибыль.
                Точность измерения - 0.01
                
                # НАЗВАНИЕ ОРГАНИЗАЦИИ
                {human_name}
                
                # ТЕКСТ НОВОСТИ
                {news_text}
                '''

                if result := llm.llm.with_structured_output(Value).invoke(
                        [
                            SystemMessage(content=main_news_prompt),
                            HumanMessage(content=prompt),
                        ],
                        config=llm.config
                ):
                    if result and result.value is not None:
                        return {'sentiment': result.value}

            except Exception as e:
                logger.log_error(
                    method_name='llm_news_sentiment_rate',
                    error=e,
                    is_telegram_send=False,
                )
    return {}


def impact_strength_rate(state: State):
    if human_name := state.get('human_name', None):
        if news_text := state.get('news_text', None):
            try:
                prompt = f'''
                # КРИТЕРИЙ ОЦЕНКИ
                impact_strength - Сила потенциального влияния на цену акций, т.е. насколько описываемые в новости события влияют на стоимость акций организации.
                Измеряется в диапазоне от 0.00 до 1.00, где:
                0.00 - нет влияния. Новость не связана с деятельностью компании;
                0.10 - минимальное влияние. Косвенное упоминание в контексте общерыночных тенденций;
                0.30 - незначительное влияние. Влияние на неосновные бизнес-процессы, репутационные риски;
                0.50 - умеренное влияние. Влияние на финансовые показатели (выручка, прибыль), операционные процессы;
                1.00 - сильное влияние. Прямое влияние на котировки акций, дивиденды, стратегические решения.
                Точность измерения - 0.01
                
                # НАЗВАНИЕ ОРГАНИЗАЦИИ
                {human_name}
                
                # ТЕКСТ НОВОСТИ
                {news_text}
                '''

                if result := llm.llm.with_structured_output(Value).invoke(
                        [
                            SystemMessage(content=main_news_prompt),
                            HumanMessage(content=prompt),
                        ],
                        config=llm.config
                ):
                    if result and result.value is not None:
                        return {'impact_strength': result.value}

            except Exception as e:
                logger.log_error(
                    method_name='llm_news_impact_strength_rate',
                    error=e,
                    is_telegram_send=False,
                )
    return {}


def mention_focus_rate(state: State):
    if human_name := state.get('human_name', None):
        if news_text := state.get('news_text', None):
            try:
                prompt = f'''
                # КРИТЕРИЙ ОЦЕНКИ
                mention_focus - Измеряет, насколько текст новости или события описываемые в новости сконцентрирован на организации.
                Измеряется в диапазоне от 0.00 до 1.00, где:
                0.00 - организация не упоминается в новости;
                0.10 - случайное упоминание в списке других организаций;
                0.20 - упоминание в качестве примера или для контекста;
                0.50 - организация - один из нескольких ключевых объектов новости;
                0.70 - организация - главный объект новости, но есть упоминания и других компаний;
                0.90 - организация упоминается в заголовке, большая часть текста посвящена ей;
                1.00 - новость полностью посвящена организации.
                Точность измерения - 0.01
                
                # НАЗВАНИЕ ОРГАНИЗАЦИИ
                {human_name}
                
                # ТЕКСТ НОВОСТИ
                {news_text}
                '''

                if result := llm.llm.with_structured_output(Value).invoke(
                        [
                            SystemMessage(content=main_news_prompt),
                            HumanMessage(content=prompt),
                        ],
                        config=llm.config
                ):
                    if result and result.value is not None:
                        return {'mention_focus': result.value}

            except Exception as e:
                logger.log_error(
                    method_name='llm_news_mention_focus_rate',
                    error=e,
                    is_telegram_send=False,
                )
    return {}


def llm_total_result(state: State):
    sentiment = state.get('sentiment', None)
    impact_strength = state.get('impact_strength', None)
    mention_focus = state.get('mention_focus', None)

    if (
            sentiment is not None and sentiment >= -1 and sentiment <= 1
            and impact_strength is not None and impact_strength >= 0 and impact_strength <= 1
            and mention_focus is not None and mention_focus >= 0 and mention_focus <= 1
    ):
        return {'structured_response': {
            'sentiment': sentiment,
            'impact_strength': impact_strength,
            'mention_focus': mention_focus,
        }}

    return {}
