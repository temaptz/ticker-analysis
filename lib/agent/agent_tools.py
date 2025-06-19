import datetime
from langchain_core.tools import tool
from lib import instruments, fundamentals, predictions, users, invest_calc, news


@tool
def get_weather(city: str) -> str:
    """
    Возвращает погоду в заданном городе
    """
    return 'Дождь'


@tool
def get_instruments_list() -> list[str]:
    """
    Получает список UID биржевых инструментов
    """
    return [instrument.uid for instrument in instruments.get_instruments_white_list()][:3]


@tool
def get_user_instruments_list() -> list[str]:
    """
    Возвращает список UID биржевых инструментов, которые есть в портфеле
    """
    return [instrument.uid for instrument in users.get_user_instruments_list()]


@tool
def get_instrument_info(uid: str) -> dict or None:
    """
    Возвращает подробную информацию о единичном биржевом инструменте. На выходе: фундаментальные показатели, текущая цена, прогноз изменения цены, оценка новостного фона относительно инструмента. На входе: UID инструмента.
    """
    instrument_uid = uid

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

        return {
            'fundamentals': {
                'currency': fundamentals_info.currency,
                'revenue_ttm': fundamentals_info.revenue_ttm,
                'ebitda_ttm': fundamentals_info.ebitda_ttm,
                'market_capitalization': fundamentals_info.market_capitalization,
                'total_debt_mrq': fundamentals_info.total_debt_mrq,
                'eps_ttm': fundamentals_info.eps_ttm,
                'pe_ratio_ttm': fundamentals_info.pe_ratio_ttm,
                'ev_to_ebitda_mrq': fundamentals_info.ev_to_ebitda_mrq,
                'dividend_payout_ratio_fy': fundamentals_info.dividend_payout_ratio_fy,
            },
            'current_price': price,
            'price_relative_change_prediction_future_days': [
                {
                    '7': prediction_7,
                    '30': prediction_30,
                    '60': prediction_60,
                    '90': prediction_90,
                    '180': prediction_180,
                    '365': prediction_365,
                }
            ],
            'news_sentiment_last_month': news.news.get_influence_score(
                instrument_uid=instrument_uid,
                start_date=datetime.datetime.now() - datetime.timedelta(days=30),
                end_date=datetime.datetime.now(),
            ),
            'ticker': instrument_info.ticker,
            'full_name': instrument_info.name,
        }
    return None


@tool
def get_instrument_balance(uid: str) -> dict or None:
    """
    Возвращает баланс единичного биржевого инструмента. На выходе: баланс инструмента в портфеле, среднюю цена покупки, потенциальная прибыль, рыночная стоимость. На входе: UID инструмента.
    """
    instrument_uid = uid

    if balance := users.get_user_instrument_balance(instrument_uid=instrument_uid):
        if invest_calc_info := invest_calc.get_invest_calc_by_instrument_uid(instrument_uid=instrument_uid):
            return {
                'balance': balance,
                'market_value': invest_calc_info['market_value'],
                'potential_profit': invest_calc_info['potential_profit'],
                'potential_profit_percent': invest_calc_info['potential_profit_percent'],
                'avg_price': invest_calc_info['avg_price'],
            }
    return None
