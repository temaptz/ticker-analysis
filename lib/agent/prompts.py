import datetime

from lib import instruments, fundamentals, predictions, news, invest_calc, users, utils


def get_system_invest_prompt() -> str:
    return f'''
    1. Ты полезный ИИ помощник.
    2. Ты эксперт в трейдинге.
    3. Даешь взвешенные и продуманные инвестиционные рекомендации.
    4. Ты анализируешь различные показатели и помогаешь принимать финансовые решения.
    5. Инструментом называют акции компании.
    6. Рассуждай пошагово.
    '''


def get_missed_data_prompt() -> str:
    return f'''
    1. "Unknown" или "None" считай отсутствующими данными.
    2. Если данные не полные или частично отсутствуют, то нужно снижать за это оценку.
    3. Если данные отсутствуют полностью, то за это оценка 0.
    4. Отсутствие каких либо данных приравнивается к их нулевой оценке.
    '''


def get_thinking_prompt() -> str:
    return f'''
    Решай поставленную задачу используя Program of Thought.
    
    Инструкции:
    1. Сначала запиши задачу в виде переменных и уравнений.
    2. Затем реализуй решение в виде кода (Python или псевдокод).
    3. Выполни код шаг за шагом, показывая результаты каждой операции.
    4. В конце дай окончательный ответ с пояснениями.
    '''


def get_instrument_info_prompt(instrument_uid: str) -> str:
    try:
        if instrument := instruments.get_instrument_by_uid(uid=instrument_uid):
            return f'''
            # НАЗВАНИЕ ИНСТРУМЕНТА
            name: {instrument.name}
            
            # ТИКЕР ИНСТРУМЕНТА
            ticker: {instrument.ticker}
            
            # UID ИНСТРУМЕНТА
            instrument_uid: {instrument.uid}
            
            # РАЗМЕР ЛОТА
            lot_size: {instruments.get_instrument_by_uid(instrument_uid).lot or 1}
            '''
    except Exception as e:
        print('ERROR get_price_prediction_prompt', e)

    return 'Инструмент не найден. Инструмент - Unknown'


def get_fundamental_prompt(instrument_uid: str) -> str:
    try:
        if i := instruments.get_instrument_by_uid(instrument_uid):
            if f := fundamentals.get_fundamentals_by_asset_uid(i.asset_uid)[0]:
                f_6_months = fundamentals.get_db_fundamentals_by_asset_uid_date_2(
                    asset_uid=i.asset_uid,
                    date=datetime.datetime.now() - datetime.timedelta(days=30 * 6)
                )
                f_12_months = fundamentals.get_db_fundamentals_by_asset_uid_date_2(
                    asset_uid=i.asset_uid,
                    date=datetime.datetime.now() - datetime.timedelta(days=30 * 12)
                )

                result = f'''
                # ТЕКУЩИЕ АКТУАЛЬНЫЕ ФУНДАМЕНТАЛЬНЫЕ ПОКАЗАТЕЛИ
                
                [
                    {{
                        "date": "{datetime.datetime.now().strftime('%Y-%m-%d')}",
                        "date_description": "Текущие фундаментальные показатели",
                        "currency": "{f.currency}",
                        "revenue_ttm": "{f.revenue_ttm}",
                        "ebitda_ttm": "{f.ebitda_ttm}",
                        "market_capitalization": "{f.market_capitalization}",
                        "total_debt_mrq": "{f.total_debt_mrq}",
                        "eps_ttm": "{f.eps_ttm}",
                        "pe_ratio_ttm": "{f.pe_ratio_ttm}",
                        "ev_to_ebitda_mrq": "{f.ev_to_ebitda_mrq}",
                        "dividend_payout_ratio_fy": "{f.dividend_payout_ratio_fy}",
                    }},
                    {{
                        "date": "{(datetime.datetime.now() - datetime.timedelta(days=30 * 6)).strftime('%Y-%m-%d')}",
                        "date_description": "Фундаментальные показатели 6 месяцев назад",
                        "currency": "{getattr(f_6_months, 'currency')}",
                        "revenue_ttm": "{getattr(f_6_months, 'revenue_ttm')}",
                        "ebitda_ttm": "{getattr(f_6_months, 'ebitda_ttm')}",
                        "market_capitalization": "{getattr(f_6_months, 'market_capitalization')}",
                        "total_debt_mrq": "{getattr(f_6_months, 'total_debt_mrq')}",
                        "eps_ttm": "{getattr(f_6_months, 'eps_ttm')}",
                        "pe_ratio_ttm": "{getattr(f_6_months, 'pe_ratio_ttm')}",
                        "ev_to_ebitda_mrq": "{getattr(f_6_months, 'ev_to_ebitda_mrq')}",
                        "dividend_payout_ratio_fy": "{getattr(f_6_months, 'dividend_payout_ratio_fy')}",
                    }},
                    {{
                        "date": "{(datetime.datetime.now() - datetime.timedelta(days=30 * 12)).strftime('%Y-%m-%d')}",
                        "date_description": "Фундаментальные показатели 12 месяцев назад",
                        "currency": "{getattr(f_12_months, 'currency')}",
                        "revenue_ttm": "{getattr(f_12_months, 'revenue_ttm')}",
                        "ebitda_ttm": "{getattr(f_12_months, 'ebitda_ttm')}",
                        "market_capitalization": "{getattr(f_12_months, 'market_capitalization')}",
                        "total_debt_mrq": "{getattr(f_12_months, 'total_debt_mrq')}",
                        "eps_ttm": "{getattr(f_12_months, 'eps_ttm')}",
                        "pe_ratio_ttm": "{getattr(f_12_months, 'pe_ratio_ttm')}",
                        "ev_to_ebitda_mrq": "{getattr(f_12_months, 'ev_to_ebitda_mrq')}",
                        "dividend_payout_ratio_fy": "{getattr(f_12_months, 'dividend_payout_ratio_fy')}",
                    }}
                ]
                
                # РАСШИФРОВКА
                
                currency - валюта
                revenue_ttm - выручка
                ebitda_ttm - EBITDA
                market_capitalization - капитализация
                total_debt_mrq - долг
                eps_ttm - EPS - прибыль на акцию
                pe_ratio_ttm - P/E - цена/прибыль
                ev_to_ebitda_mrq - EV/EBITDA - стоимость компании / EBITDA
                dividend_payout_ratio_fy - DPR - коэффициент выплаты дивидендов
                                    
                # ИНСТРУКЦИЯ

                1. **Выручка и EBITDA** — оцени динамику за 6 и 12 месяцев:
                   - Сравни текущие значения с прошлыми периодами.
                   - Если наблюдается устойчивый рост, это признак расширения бизнеса.
                   - Снижение или стагнация — потенциальный сигнал замедления развития.
                
                2. **Маржинальность** — сравни EBITDA с выручкой во всех периодах:
                   - Рост маржи (отношения EBITDA к выручке) = повышение операционной эффективности.
                   - Падение маржи может сигнализировать о росте издержек или снижении ценовой силы.
                
                3. **Капитализация** — оцени, как изменилась рыночная стоимость компании за год и полгода:
                   - Рост капитализации при стабильных или снижающихся показателях — возможный признак переоценки.
                   - Снижение капитализации при стабильной прибыли — может говорить о рыночной недооценке.
                
                4. **Долг** — анализируй его динамику относительно EBITDA:
                   - Если долг растёт быстрее, чем прибыль, это тревожный сигнал.
                   - Снижение долга — положительный фактор, особенно при стабильной выручке.
                
                5. **EPS (прибыль на акцию)** — ключевой показатель для акционеров:
                   - Сравни тренд: если EPS растёт, это усиливает инвестиционную привлекательность.
                   - При стагнации или снижении стоит оценить причины и риски.
                
                6. **P/E (Price-to-Earnings)** — обрати внимание на изменение:
                   - Рост P/E при падении EPS — сигнал переоценки.
                   - Снижение P/E при росте прибыли — потенциальная возможность для покупки.
                
                7. **EV/EBITDA** — сравни по трем периодам:
                   - Если EV/EBITDA растёт быстрее, чем EBITDA — компания может становиться дороже без роста эффективности.
                   - Снижение мультипликатора на фоне стабильной или растущей EBITDA — позитивный сигнал.
                
                8. **DPR (коэффициент выплаты дивидендов)** — оцени изменение политики:
                   - Рост DPR при падающем EPS может быть устойчиво опасным для будущих дивидендов.
                   - Снижение DPR может означать стремление к реинвестициям или консервативный подход.
                
                9. **Сравнение трендов**:
                   - Зафиксируй, какие показатели демонстрируют позитивную динамику (рост), а какие — ухудшение.
                   - Выдели ключевые сдвиги за последние 6 и 12 месяцев.
                
                10. **Финальный вывод**:
                   - Насколько сбалансированы текущие показатели?
                   - Есть ли устойчивые сигналы роста или признаки замедления/рисков?
                   - Оцени, являются ли акции компании перспективными для покупки или, наоборот, подвержены падению в ближайшие 6–12 месяцев.
                '''

                return result
    except Exception as e:
        print('ERROR get_fundamental_prompt', e)

    return 'Фундаментальные показатели не найдены. Фундаментальные показатели - Unknown'


def get_price_prediction_prompt(instrument_uid: str) -> str:
    try:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        current_price = instruments.get_instrument_last_price_by_uid(uid=instrument_uid)
        prediction_week = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=7)
        ), 4)
        prediction_2_weeks = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=14)
        ), 4)
        prediction_3_weeks = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=21)
        ), 4)
        prediction_month = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=30)
        ), 4)
        prediction_2_months = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=60)
        ), 4)
        prediction_3_months = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=90)
        ), 4)
        prediction_6_months = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=180)
        ), 4)
        prediction_year = utils.round_float(predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=365)
        ), 4)

        print('PRICE PREDICTION PROMPT DATA current_price', current_price)
        print('PRICE PREDICTION PROMPT DATA prediction_week', prediction_week)
        print('PRICE PREDICTION PROMPT DATA prediction_2_weeks', prediction_2_weeks)
        print('PRICE PREDICTION PROMPT DATA prediction_3_weeks', prediction_3_weeks)
        print('PRICE PREDICTION PROMPT DATA prediction_month', prediction_month)
        print('PRICE PREDICTION PROMPT DATA prediction_2_months', prediction_2_months)
        print('PRICE PREDICTION PROMPT DATA prediction_3_months', prediction_3_months)
        print('PRICE PREDICTION PROMPT DATA prediction_6_months', prediction_6_months)
        print('PRICE PREDICTION PROMPT DATA prediction_year', prediction_year)

        if current_price and (
                prediction_week
                or prediction_2_weeks
                or prediction_3_weeks
                or prediction_month
                or prediction_2_months
                or prediction_3_months
                or prediction_6_months
                or prediction_year
        ):
            return f'''
            # ТЕКУЩАЯ РЫНОЧНАЯ ЦЕНА ИНСТРУМЕНТА
            
            current_price: {current_price}
            
            # ПРОГНОЗ ОТНОСИТЕЛЬНОГО ИЗМЕНЕНИЯ ЦЕНЫ - price_prediction
            
            {{
                "1_week": {{
                    "prediction_relative_percent": "{'+' if prediction_week > 0 else ''}{utils.round_float(prediction_week, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 1 неделю"
                }},
                "2_weeks": {{
                    "prediction_relative_percent": "{'+' if prediction_2_weeks > 0 else ''}{utils.round_float(prediction_2_weeks, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 2 недели"
                }},
                "3_weeks": {{
                    "prediction_relative_percent": "{'+' if prediction_3_weeks > 0 else ''}{utils.round_float(prediction_3_weeks, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 3 недели"
                }},
                "1_month": {{
                    "prediction_relative_percent": "{'+' if prediction_month > 0 else ''}{utils.round_float(prediction_month, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 1 месяц"
                }},
                "2_months": {{
                    "prediction_relative_percent": "{'+' if prediction_2_months > 0 else ''}{utils.round_float(prediction_2_months, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 2 месяца"
                }},
                "3_months": {{
                    "prediction_relative_percent": "{'+' if prediction_3_months > 0 else ''}{utils.round_float(prediction_3_months, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 3 месяца"
                }},
                "6_months": {{
                    "prediction_relative_percent": "{'+' if prediction_6_months > 0 else ''}{utils.round_float(prediction_6_months, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 6 месяцев"
                }},
                "1_year": {{
                    "prediction_relative_percent": "{'+' if prediction_year > 0 else ''}{utils.round_float(prediction_year, 5) * 100}%",
                    "description": "Прогноз относительного изменения цены акции через 1 год"
                }}
            }}
            
            # ПРИМЕЧАНИЕ
            
            1. Прогноз относительного изменения цены вычисляется по формуле: prediction_relative_percent = ([прогнозируемая_цена] - [текущая_цена]) / [текущая_цена]) * 100%;
            2. Прогноз относительного изменения цены prediction_relative_percent является точным прогнозом цены в будущем;
            3. prediction_relative_percent надежная оценка которую нужно опираться при принятии финансового решения.
            
            # ИДЕАЛЬНЫЙ ПРИМЕР ДЛЯ ПОКУПКИ
            Пример, за который можно ставить высшую оценку по критерию прогноза цены если цель - выгодная покупка
            
            {{ 
                "1_week": {{ "prediction_relative_percent": "5%" }}, 
                "2_weeks": {{ "prediction_relative_percent": "7.5%" }}, 
                "3_weeks": {{ "prediction_relative_percent": "10%" }}, 
                "1_month": {{ "prediction_relative_percent": "12.5%" }}, 
                "2_months": {{ "prediction_relative_percent": "15%" }}, 
                "3_months": {{ "prediction_relative_percent": "17.5%" }}, 
                "6_months": {{ "prediction_relative_percent": "20%" }}, 
                "1_year": {{ "prediction_relative_percent": "22.5%" }}
            }}
            
            # ИДЕАЛЬНЫЙ ПРИМЕР ДЛЯ ПРОДАЖИ
            Пример, за который можно ставить высшую оценку по критерию прогноза цены если цель - выгодная продажа
            
            {{ 
                "1_week": {{ "prediction_relative_percent": "-5%" }}, 
                "2_weeks": {{ "prediction_relative_percent": "-7.5%" }}, 
                "3_weeks": {{ "prediction_relative_percent": "-10%" }}, 
                "1_month": {{ "prediction_relative_percent": "-12.5%" }}, 
                "2_months": {{ "prediction_relative_percent": "-15%" }}, 
                "3_months": {{ "prediction_relative_percent": "-17.5%" }}, 
                "6_months": {{ "prediction_relative_percent": "-20%" }}, 
                "1_year": {{ "prediction_relative_percent": "-22.5%" }}
            }}
            '''
    except Exception as e:
        print('ERROR get_price_prediction_prompt', e)

    return 'Прогноз цены не найден. Прогноз цены - Unknown'


def get_news_prompt(instrument_uid: str) -> str:
    try:
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        news_rate_week_0 = news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=now - datetime.timedelta(days=7),
            end_date=now,
        )
        news_rate_week_1 = news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=now - datetime.timedelta(days=14),
            end_date=now - datetime.timedelta(days=8),
        )
        news_rate_week_2 = news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=now - datetime.timedelta(days=21),
            end_date=now - datetime.timedelta(days=15),
        )
        news_rate_week_3 = news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=now - datetime.timedelta(days=28),
            end_date=now - datetime.timedelta(days=22),
        )

        print('NEWS PROMPT DATA news_rate_week_1', news_rate_week_0)
        print('NEWS PROMPT DATA news_rate_week_1', news_rate_week_1)
        print('NEWS PROMPT DATA news_rate_week_2', news_rate_week_2)
        print('NEWS PROMPT DATA news_rate_week_3', news_rate_week_3)

        if news_rate_week_0 or news_rate_week_1 or news_rate_week_2 or news_rate_week_3:
            return f'''
            # РЕЙТИНГ НОВОСТНОГО ФОНА
            {{
                "d0_7": {{
                    "influence_score": {news_rate_week_0},
                    "description": "Рейтинг новостного фона за период от 0 до 7 дней до текущей даты"
                }},
                "d8_14": {{
                    "influence_score": {news_rate_week_1},
                    "description": "Рейтинг новостного фона за период от 8 до 14 дней до текущей даты"
                }},
                "d15_21": {{
                    "influence_score": {news_rate_week_2},
                    "description": "Рейтинг новостного фона за период от 15 до 21 дней до текущей даты"
                }},
                "d22_28": {{
                    "influence_score": {news_rate_week_3},
                    "description": "Рейтинг новостного фона за период от 22 до 28 дней до текущей даты"
                }}
            }}
            
            
            # ПРИМЕЧАНИЕ
            
            1. Рейтинг новостного фона influence_score - вещественное число
            2. influence_score вычисляется путем сложения вычисленного influence_score_item каждой отдельной новости имеющей отношение к субъекту за указанный период времени.
            3. Рейтинг новостного фона influence_score_item для каждой отдельной новости вычисляется по формуле influence_score_item = sentiment * impact_strength * mention_focus, где:
             - sentiment - отношение новости по отношению к субъекту от -1 до 1;
             - impact_strength - силу влияния новости на цену акции от 0 до 1;
             - mention_focus - сфокусированность новости на субъекте от 0 до 1.
            4. influence_score отражает силу и направление(положительное или отрицательное) влияния новостного фона за период времени на цену акции.
            
            # ИДЕАЛЬНЫЙ ПРИМЕР ДЛЯ ПОКУПКИ
            Пример, за который можно ставить высшую оценку по критерию оценки новостного фона если цель - выгодная покупка
            
            {{
                "d0_7": {{
                    "influence_score": 5,
                }},
                "d8_14": {{
                    "influence_score": 3.7,
                }},
                "d15_21": {{
                    "influence_score": 3,
                }},
                "d22_28": {{
                    "influence_score": 1.5,
                }}
            }}
            
            # ИДЕАЛЬНЫЙ ПРИМЕР ДЛЯ ПРОДАЖИ
            Пример, за который можно ставить высшую оценку по критерию оценки новостного фона если цель - выгодная продажа
            
            {{
                "d0_7": {{
                    "influence_score": -5,
                }},
                "d8_14": {{
                    "influence_score": -3.5,
                }},
                "d15_21": {{
                    "influence_score": -1.7,
                }},
                "d22_28": {{
                    "influence_score": -1,
                }}
            }} 
            '''
    except Exception as e:
        print('ERROR get_news_prompt', e)

    return 'Оценка рейтинга новостного фона отсутствует. Рейтинг новостного фона - Unknown'


def get_profit_calc_prompt(instrument_uid: str) -> str:
    try:
        calc = invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=instrument_uid, account_id=users.get_analytics_account().id)

        if calc:
            return f'''
            # ПОТЕНЦИАЛЬНАЯ ВЫГОДА ОТ ПРОДАЖИ ИНСТРУМЕНТА
            
            Текущая цена - current_price: {calc['current_price'] or 'Unknown'}
            Баланс - balance: {calc['balance'] or 'Unknown'}
            Общая стоимость бумаг - market_value: {calc['market_value'] or 'Unknown'}
            Потенциальная прибыль при продаже всех бумаг - potential_profit: {calc['potential_profit'] or 'Unknown'}
            Потенциальная прибыль в процентах при продаже всех бумаг - potential_profit_percent: {calc['potential_profit_percent'] or 'Unknown'}
            Средняя цена покупки - avg_price: {calc['avg_price'] or 'Unknown'}
            
            # ИДЕАЛЬНЫЙ ПРИМЕР ДЛЯ ПРОДАЖИ
            Пример за который нужно ставить высшую оценку по критерию потенциальной выгоды если цель - выгодная продажа
            
            {{
                "current_price": 105,
                "balance": 500,
                "market_value": 52500,
                "potential_profit": 45500,
                "potential_profit_percent": 50,
                "avg_price": 70
            }}
            
            # НЕВЫГОДНЫЙ ПРИМЕР ДЛЯ ПРОДАЖИ
            Пример за который нужно ставить низшую оценку по критерию потенциальной выгоды если цель - выгодная продажа
            
            {{
                "current_price": 30,
                "balance": 500,
                "market_value": 15000,
                "potential_profit": -20000,
                "potential_profit_percent": -55,
                "avg_price": 70
            }}
            '''
    except Exception as e:
        print('ERROR get_invest_recommendation_prompt', e)

    return 'Оценка потенциальной выгоды от продажи инструмента отсутствует. Оценка - Unknown'
