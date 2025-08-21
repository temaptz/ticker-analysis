from typing import TypedDict
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
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
    instrument_uid: str
    invest_calc_rate: RatePercentWithConclusion
    price_prediction_rate: RatePercentWithConclusion
    structured_response: RatePercentWithConclusion


def update_recommendations():
    graph_sell = get_sell_rank_graph()

    for i in users.sort_instruments_for_sell(
            instruments_list=users.get_user_instruments_list(account_id=users.get_analytics_account().id)
    ):
        try:
            result = graph_sell.invoke(
                input={'instrument_uid': i.uid},
                debug=True,
                config=llm.config,
            )

            if structured_response := result.get('structured_response', None):
                if structured_response.rate:
                    db_2.instrument_tags_db.upset_tag(
                        instrument_uid=i.uid,
                        tag_name='llm_sell_rate',
                        tag_value=structured_response.rate,
                    )

                    logger.log_info(
                        message=f'Сохранена оценка продажи {i.name}\nОценка: {structured_response.rate}\nКомментарий: {structured_response.final_conclusion}',
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
    if instrument_uid := state.get('instrument_uid', None):
        prompt = f'''
        # ЗАДАНИЕ
        
        Как специалист по биржевой торговле проанализируй потенциальную выгоду при продаже инструмента.
        
        # ИНСТРУКЦИЯ
        
        1. Главный критерий оценки - потенциальная прибыль в абсолютном и процентном выражении (potential_profit, potential_profit_percent).
        2. Для средней оценки потенциальная прибыль должна быть строго положительной.
        2. Для хорошей оценки потенциальная прибыль должна быть очень высокой.
        3. Для хорошей оценки важно чтобы текущая цена (current_price) была значительно выше средней цены покупки инструмента (avg_price).
        4. Итоговая оценка - одно число от 0 до 100, где:
           - 0-10 - отрицательна потенциальная прибыль, продажа с убытком;
           - 11-25 - потенциальная прибыль меньше 5%, продажа с малой прибылью;
           - 26-50 - низкая потенциальная прибыль, продажа с умеренной прибылью;
           - 51-75 - умеренная потенциальная прибыть, выгодная продажа с высокой прибылью;
           - 76-100 - высокая потенциальная прибыть, выгодная продажа с очень высокой прибылью.   
        5. Снижай оценку при отсутствии информации, если данные полностью отсутствуют, от оценка 0.
           
        # ФОРМАТ ОТВЕТА
        
        Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
        '''


        print('HUMAN MESSAGE invest_calc_rate', prompt)

        try:
            if result := llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                    [
                        SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                        SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                        SystemMessage(content=agent.prompts.get_thinking_prompt()),
                        HumanMessage(content=agent.prompts.get_profit_calc_prompt(instrument_uid=instrument_uid)),
                        HumanMessage(content=prompt),
                    ],
                    config=llm.config
            ):
                if result and result.rate is not None:
                    logger.log_info(message=f'LLM INVEST CALC RATE IS: {result}')
                    return {'invest_calc_rate': result}

        except Exception as e:
            logger.log_error(
                method_name='llm_invest_calc_rate',
                error=e,
                is_telegram_send=False,
            )
    return {}


def llm_price_prediction_rate(state: State):
    if instrument_uid := state.get('instrument_uid', None):
        prompt = f'''
        # ЗАДАНИЕ
        
        Как специалист по трейдингу оцени насколько выгодна продажа акций именно сейчас.
        
        # ИНСТРУКЦИЯ
        
        1. Проанализируй изменение цены на каждом интервале времени.
        2. Учитывай что акции выгоднее продавать при высокой цене и перед трендом на снижение.
        3. Если в ближайшем будущем согласно прогнозу цена будет расти, то продажа сейчас менее выгодна.
        4. Достаточный тренд на снижение в ближайшем будущем не меньше месяца увеличивает вероятность выгодной продажи и оценку.
        5. Оцени, насколько выгодна продажа акций именно сейчас.
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
            
            Как специалист по биржевой торговле оцени насколько выгодна продажа этого инструмента именно сейчас.

            # ИНСТРУКЦИЯ
            
            1. Учитывай все показатели: предварительные оценки и комментарии.
            2. Самый важный показатель на который надо опираться в ответе - оценка потенциальной выгоды invest_rate.
            3. Второй по значимости показатель - оценка оптимального момента продажи price_prediction_rate.
            3. Присвой итоговую оценку от 0 до 100, где:
               - 0-25 - все оценки низкие, продажа сейчас не выгодна;
               - 26-50 - оценки ниже среднего, продажа сейчас умеренно выгодна, момент продажи не удачный;
               - 51-74 - оценки выше среднего, продажа сейчас выгодна, момент для продажи средне удачный.
               - 75-100 - все оценки высокие, сейчас выгодный и удачный момент для продажи.
            5. Итоговая оценка будет использоваться для сравнения между инструментами.
            6. Отсутствующие данные приравниваются к 0 оценке.
            7. Учитывай полученные ранее сырые данные.
            
            # ФОРМАТ ОТВЕТА
            
            Ответ - Итоговый краткий вывод и итоговая оценка целое число от 0 до 100.
            '''


            print('HUMAN MESSAGE total_buy_rate', prompt)

            try:
                if result := llm.llm.with_structured_output(RatePercentWithConclusion).invoke(
                        [
                            SystemMessage(content=agent.prompts.get_system_invest_prompt()),
                            SystemMessage(content=agent.prompts.get_missed_data_prompt()),
                            SystemMessage(content=agent.prompts.get_thinking_prompt()),
                            HumanMessage(content=agent.prompts.get_instrument_info_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=agent.prompts.get_price_prediction_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=agent.prompts.get_profit_calc_prompt(instrument_uid=instrument_uid)),
                            HumanMessage(content=prompt),
                        ],
                        config=llm.config
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
