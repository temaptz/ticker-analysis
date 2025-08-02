import datetime
import time
from typing import TypedDict, Annotated

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_experimental.graph_transformers.llm import system_prompt
from langchain_experimental.plan_and_execute import PlanAndExecute, load_chat_planner, load_agent_executor
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel
from tinkoff.invest import Instrument, StatisticResponse
from lib import instruments, fundamentals, users, predictions, news, serializer, agent, utils, db_2, logger, forecasts, types_util
from lib.agent import models, llm, planner


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
    graph = get_news_rank_graph()

    for i in instruments.get_instruments_white_list():
        try:
            if human_name := instruments.get_instrument_human_name(uid=i.uid):
                if n := news.news.get_last_unrated_news_by_instrument_uid(instrument_uid=i.uid):
                    graph_input: State = {
                        'human_name': human_name,
                        'news_text': f'Заголовок:\n{n.title}\n\nТекст:\n{n.text}',
                    }
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
                            n_rate = types_util.NewsRate2(
                                sentiment=sentiment,
                                impact_strength=impact_strength,
                                mention_focus=mention_focus,
                            )

                            db_2.news_rate_2_db.insert_or_update_rate(
                                news_uid=n.news_uid,
                                instrument_uid=i.uid,
                                news_rate=n_rate,
                                model_name=llm.model_name,
                                generation_time_sec=(end - start),
                            )

                            logger.log_info(
                                message=f'Сохранена оценка новости с заголовком:\n{n.title}\nНа организацию:\n{human_name}\nОценка: {serializer.to_json(n_rate)}',
                                is_send_telegram=True,
                            )
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
При подготовке ответа используй механизм Tree of Thoughts
'''


def sentiment_rate(state: State):
    if human_name := state.get('human_name', None):
        if news_text := state.get('news_text', None):
            try:
                prompt = f'''
                # КРИТЕРИЙ ОЦЕНКИ
                sentiment - Тон новости относительно организации, насколько событие описываемое в новости положительно или отрицательно по отношению к организации.
                Измеряется в диапазоне от -1.00 до 1.00, где:
                -1.00 - отрицательный тон, говорится о неудачах и проблемах компании;
                -0.90 - отрицательный тон, говорится об отсутствии перспектив роста компании;
                0.00 - нейтральный тон;
                0.10 - критический тон, но с позитивным финальным выводом;
                1.00 - положительный тон, говорится о успехах или достижениях или перспективах компании в положительном ключе.
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
                0.00 - описываемые в новости события не влияют на компанию;
                0.50 - описываемые в новости события влияют на финансы компании;
                1.00 - описываемые в новости события влияют на стоимость акций.
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
                0.10 - несущественное упоминание в списке других организаций;
                0.20 - упоминание не акцентировано, организация упоминается в новости, для контекста, не основной фокус;
                0.50 - средний фокус, роль организации важна в общем смысле новости;
                0.70 - организация многократно упоминается в новости.
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
