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
    logger.log_info(
        message='LANGSMITH DEBUG RECOMMENDATIONS SELL',
        output={
            'LANGSMITH_TRACING': os.environ['LANGSMITH_TRACING'],
            'LANGSMITH_ENDPOINT': os.environ['LANGSMITH_ENDPOINT'],
            'LANGSMITH_API_KEY': os.environ['LANGSMITH_API_KEY'],
            'LANGSMITH_PROJECT': os.environ['LANGSMITH_PROJECT'],
        },
        is_send_telegram=True,
    )

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
        
        Как специалист по трейдингу проанализируй и оцени насколько выгодна продажа актива именно сейчас.
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй изменение цены на каждом интервале времени.
        2. Учитывай что актив выгоднее продавать при высокой цене и перед трендом на снижение.
        3. Если в ближайшем будущем согласно прогнозу цена будет расти, то продажа сейчас менее выгодна.
        4. Достаточный тренд на снижение в ближайшем будущем не меньше месяца увеличивает вероятность выгодной продажи и оценку.
        5. Оцени, насколько выгодна продажа актива именно сейчас.
        6. Присвой итоговую числовую оценку выгодной продажи целое число от 0 до 100, где:
           - 0-25 - прогноз изменения цены на ближайший месяц указывает на стабильный рост, продажа в ближайшее время не выгодна;
           - 26-74 - в ближайший месяц возможен потенциал роста, сейчас продажа может быть не выгодна;
           - 75-100 - прогноз изменения цены на ближайший месяц стабильно отрицательный, сейчас оптимальный момент для продажи.
        7. На основе шкалы данной инструкции построй собственную более развернутую шкалу и дай по ней окончательную точную оценку.
        8. В конце кратко обобщи все рассуждение сформулируй итоговый вывод и итоговую оценку целое число от 0 до 100.
        
        
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
                        HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid, is_for_sell=True)),
                        HumanMessage(content=prompt),
                    ],
                    config=agent.llm.config,
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


def llm_total_sell_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        invest_calc = state.get('invest_calc_rate', None)
        price_prediction = state.get('price_prediction_rate', None)
        invest_rate = invest_calc.rate if (invest_calc and invest_calc.rate) else None
        invest_rate_conclusion = invest_calc.final_conclusion if (invest_calc and invest_calc.final_conclusion) else None
        price_prediction_rate = price_prediction.rate if (price_prediction and price_prediction.rate) else None
        price_prediction_conclusion = price_prediction.final_conclusion if (price_prediction and price_prediction.final_conclusion) else None

        if invest_rate or price_prediction_rate:
            prompt = f'''
            # ПРЕДВАРИТЕЛЬНЫЕ ОЦЕНКИ

            Оценка потенциальной выгоды при продаже - invest_rate: {invest_rate or 'Unknown'} (0-100)
            Оценка оптимального момента продажи - price_prediction_rate: {price_prediction_rate or 'Unknown'} (0-100)
            
            
            # КОММЕНТАРИИ ПО ОЦЕНКЕ ПОТЕНЦИАЛЬНОЙ ВЫГОДЫ
                        
            {invest_rate_conclusion or 'Unknown'}
            
            # КОММЕНТАРИИ ПО ОЦЕНКЕ ОПТИМАЛЬНОГО МОМЕНТА ПРОДАЖИ
            
            {price_prediction_conclusion or 'Unknown'}
            
            # ЗАДАНИЕ
            
            Как специалист по биржевой торговле проанализируй все показатели и оцени насколько выгодна продажа этого актива именно сейчас.

            # ИНСТРУКЦИЯ
            
            1. Учитывай все показатели: предварительные оценки и комментарии.
            2. Самый важный показатель на который надо опираться в ответе - оценка потенциальной выгоды invest_rate.
            3. Второй по значимости показатель - оценка оптимального момента продажи price_prediction_rate.
            3. Присвой итоговую оценку от 0 до 100, где:
               - 0-25 - все оценки низкие, продажа сейчас не выгодна;
               - 26-50 - оценки ниже среднего, продажа сейчас умеренно выгодна, момент продажи не удачный;
               - 51-74 - оценки выше среднего, продажа сейчас выгодна, момент для продажи средне удачный.
               - 75-100 - все оценки высокие, сейчас выгодный и удачный момент для продажи.
            5. Итоговая оценка будет использоваться для сравнения между активами.
            6. Отсутствующие данные приравниваются к 0 оценке.
            7. Учитывай полученные ранее сырые данные.
            4. На основе шкалы данной инструкции построй собственную более развернутую шкалу и дай по ней окончательную точную оценку.
            
            # ФОРМАТ ОТВЕТА
            
            Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
            '''


            print('HUMAN MESSAGE total_buy_rate', prompt)

            try:
                if result := agent.llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                        [
                            SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                            SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                            SystemMessage(content=agent.prompts.get_thinking_prompt()),
                            HumanMessage(content=agent.prompts.get_instrument_info_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid, is_for_sell=True)),
                            HumanMessage(content=agent.prompts.get_profit_calc_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=prompt),
                        ],
                        config=agent.llm.config
                ):
                    if result and result.rate is not None:
                        logger.log_info(message=f'LLM TOTAL SELL RATE IS: {result.rate}')
                        return {'structured_response': result}

            except Exception as e:
                logger.log_error(
                    method_name='llm_total_sell_rate',
                    error=e,
                    is_telegram_send=False,
                )
    return {}
