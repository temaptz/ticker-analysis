from langchain_community.llms.yandex import YandexGPT
from langchain.agents import initialize_agent, AgentType
from langchain.tools import tool
from functools import reduce
from lib import cache, instruments, fundamentals, predictions, users, invest_calc
from const import Y_API_SECRET, Y_API_FOLDER_ID
import datetime

yandex_gpt = YandexGPT(api_key=Y_API_SECRET, folder_id=Y_API_FOLDER_ID, temperature=0.3, model_name='yandexgpt-lite')

@tool(description='Получает список инструментов. Для каждого инструмента выводит название и UID инструмента.')
def get_instruments_list(dummy: str = '') -> list[str]:
    instruments_list = []

    for instrument in instruments.get_instruments_white_list():
        instruments_list.append(instrument.uid)

    return instruments_list


@tool(description='Получает подробную информацию о единичном инструменте. На выходе: фундаментальные показатели, текущую цену и прогнозируемое относительное изменение цены каждого инструмента. На входе: UID инструмента.')
def get_instrument_info(uid: str) -> str or None:
    instrument_uid = uid.strip('"').strip("'")

    if instrument_info := instruments.get_instrument_by_uid(uid=instrument_uid):
        fundamentals_resp = fundamentals.get_fundamentals_by_asset_uid(asset_uid=instrument_info.asset_uid)
        fundamentals_info = fundamentals_resp[0] if fundamentals_resp and len(fundamentals_resp) > 0 else None
        price = instruments.get_instrument_last_price_by_uid(uid=instrument_uid)
        now = datetime.datetime.now(datetime.timezone.utc)
        prediction_7 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=7)
        )
        prediction_30 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=30)
        )
        prediction_60 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=60)
        )
        prediction_90 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=90)
        )
        prediction_180 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=180)
        )
        prediction_365 = predictions.get_relative_predictions_consensus(
            instrument_uid=instrument_uid,
            date_target=now + datetime.timedelta(days=365)
        )

        return f'''
        Фундаментальные показатели:
        Валюта: {safe_get(fundamentals_info, 'currency')};
        Выручка: {safe_get(fundamentals_info, 'revenue_ttm')};
        EBITDA: {safe_get(fundamentals_info, 'ebitda_ttm')};
        Капитализация: {safe_get(fundamentals_info, 'market_capitalization')};
        Долг: {safe_get(fundamentals_info, 'total_debt_mrq')};
        EPS — прибыль на акцию: {safe_get(fundamentals_info, 'eps_ttm')};
        P/E — цена/прибыль: {safe_get(fundamentals_info, 'pe_ratio_ttm')};
        EV/EBITDA — стоимость компании / EBITDA: {safe_get(fundamentals_info, 'ev_to_ebitda_mrq')};
        DPR — коэффициент выплаты дивидендов: {safe_get(fundamentals_info, 'dividend_payout_ratio_fy')};
        
        Текущая цена лота: {price};
        
        Предсказание изменения цены лота на неделю вперед: {format_percent(prediction_7)};
        Предсказание изменения цены лота на месяц вперед: {format_percent(prediction_30)};
        Предсказание изменения цены лота на два месяца вперед: {format_percent(prediction_60)};
        Предсказание изменения цены лота на три месяца вперед: {format_percent(prediction_90)};
        Предсказание изменения цены лота на полгода вперед: {format_percent(prediction_180)};
        Предсказание изменения цены лота на год вперед: {format_percent(prediction_365)};
        
        Полное название инcтрумента: {safe_get(instrument_info, 'name')};
        Тикер инcтрумента (краткое название): {safe_get(instrument_info, 'ticker')};
        UID инcтрумента: {instrument_uid};
        '''
    return None


@tool(description='Получает баланс единичного инструмента. На выходе: баланс инструмента в портфеле, среднюю цену покупки, потенциальную прибыль, рыночную стоимость. На входе: UID инструмента.')
def get_instrument_balance(uid: str) -> str or None:
    instrument_uid = uid.strip('"').strip("'")

    if instrument_info := instruments.get_instrument_by_uid(uid=instrument_uid):
        if balance := users.get_user_instrument_balance(instrument_uid=instrument_uid):
            if invest_calc_info := invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=instrument_uid):
                return f'''
                Баланс в портфеле: {balance} шт;
                Рыночная стоимость: {invest_calc_info['market_value']} {instrument_info.currency};
                Потенциальная прибыль от продажи: {invest_calc_info['potential_profit']} {instrument_info.currency};
                Потенциальная прибыль от продажи в процентах: {invest_calc_info['potential_profit_percent']};
                Средняя цена покупки: {invest_calc_info['avg_price']} {instrument_info.currency};
                '''
    return 'Баланс в портфеле: 0 шт;'


def safe_get(d, *keys):
    try:
        return reduce(
            lambda acc, key: (
                acc.get(key) if isinstance(acc, dict)
                else getattr(acc, key, {})
                if hasattr(acc, key)
                else {}
            ),
            keys,
            d
        ) or '—'
    except (AttributeError, KeyError, TypeError):
        return '—'


def format_percent(num: float) -> str:
    try:
        return f'{round(float(num) * 100, 2)} %'
    except Exception as e:
        print('ERROR format_percent', e)

    return '-'


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_invest_recommendation() -> str or None:
    result = agent.invoke(f'''
    Ты финансовый эксперт. Даешь качественные инвестиционные рекомендации.
    Используй список инструментов с фондовой биржи.
    Проанализируй каждый инструмент в списке и оцени его как инвестиционную рекомендацию.
    При анализе используй данные о фундаментальных показателях, текущей цене, прогнозируемом относительном изменении цены.
    На основе своей оценки составь рейтинг из трех инструментов, которые сейчас выгоднее всего купить для продажи в будущем. 
    Отвечай на русском языке. Итоговый ответ должен быть подробным и объясненным.
    ''')

    print('Итоговый ответ по инвестиционным рекомендациям get_invest_recommendation:')
    print(result['output'] if result and result['output'] else None)

    return result['output'] if result and result['output'] else None


# @cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_invest_sell_recommendation() -> str or None:
    result = agent.invoke(f'''
    Ты финансовый эксперт. Даешь качественные и всесторонне взвешенные инвестиционные рекомендации.
    Используй список инструментов с фондовой биржи.
    Проанализируй каждый инструмент в списке и оцени насколько оптимальный сейчас момент для выгодной продажи.
    При анализе используй следующие данные: текущая цена, прогнозируемое относительное изменение цены, текущий баланс инструмента в портфеле, среднюю цену покупки, потенциальную прибыль, рыночную стоимость.
    На основе своей оценки составь рейтинг из трех инструментов, которые сейчас выгоднее всего продать и для которых именно сейчас оптимальный момент продажи. 
    Отвечай на русском языке. Итоговый ответ должен быть подробным и объясненным.
    ''')

    print('Итоговый ответ по инвестиционным рекомендациям get_invest_sell_recommendation:')
    print(result['output'] if result and result['output'] else None)

    return result['output'] if result and result['output'] else None


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_instrument_invest_recommendation(instrument_uid: str) -> str or None:
    result = agent.invoke(f'''
    Ты финансовый эксперт. Даешь качественные инвестиционные рекомендации.
    Используй список инструментов с фондовой биржи.
    Проанализируй подробно инструмент с UID {instrument_uid} и оцени его как инвестиционную рекомендацию.
    При анализе используй данные о фундаментальных показателях, текущей цене, прогнозируемом относительном изменении цены.
    В ответе должна быть однозначная рекомендация, что делать с данной бумагой, покупать, продавать или держать.
    Далее дай подробное объяснение своему выбору.
    Отвечай на русском языке.
    ''')

    print('Итоговый ответ по инвестиционным рекомендациям get_instrument_invest_recommendation:')
    print(result['output'] if result and result['output'] else None)

    return result['output'] if result and result['output'] else None


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_instrument_invest_short_recommendation(instrument_uid: str) -> str or None:
    result = agent.invoke(f'''
    Ты финансовый эксперт. Даешь качественные инвестиционные рекомендации.
    Используй список инструментов с фондовой биржи.
    Проанализируй подробно инструмент с UID {instrument_uid} и оцени его как инвестиционную рекомендацию.
    При анализе используй данные о фундаментальных показателях, текущей цене, прогнозируемом относительном изменении цены.
    В ответе должна быть однозначная рекомендация, что делать с данной бумагой, покупать, продавать или держать.
    Ответ должен быть одним словом.
    Отвечай на русском языке.
    ''')

    print('Итоговый ответ по инвестиционным рекомендациям get_instrument_invest_short_recommendation:')
    print(result['output'] if result and result['output'] else None)

    return result['output'] if result and result['output'] else None

agent = None

# agent = initialize_agent(
#     agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
#     tools=[get_instruments_list, get_instrument_info, get_instrument_balance],
#     llm=yandex_gpt,
#     verbose=True,
#     handle_parsing_errors=True,
#     max_iterations=60,
#     early_stopping_method='generate',
# )
