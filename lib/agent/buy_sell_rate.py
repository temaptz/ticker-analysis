import datetime
from lib import users, serializer, db_2, agent, news, invest_calc, utils


def calculate_total_buy_rate(
    fundamental_rate: int = None,
    fundamental_conclusion: str = None,
    price_prediction_rate: int = None,
    price_prediction_conclusion: str = None,
    news_rate: int = None,
    news_conclusion: str = None,
    macd_rate: int = None,
    macd_conclusion: str = None,
    instrument_uid: str = None,
):
    is_in_favorites = users.get_is_in_favorites(instrument_uid=instrument_uid) if instrument_uid else False

    if fundamental_rate or price_prediction_rate:
        try:
            weights = {
                'macd_buy_rate': 7,
                'price_prediction_rate': 5,
                'fundamental_rate': 2,
                'news_rate': 1,
                'favorites': 0.1,
            }
            calc_rate = int(
                (
                        (fundamental_rate or 0) * weights['fundamental_rate']
                        + (price_prediction_rate or 0) * weights['price_prediction_rate']
                        + (news_rate or 0) * weights['news_rate']
                        + (100 if is_in_favorites else 0) * weights['favorites']
                        + (macd_rate or 0) * weights['macd_buy_rate']
                )
                / (
                        weights['fundamental_rate']
                        + weights['price_prediction_rate']
                        + weights['news_rate']
                        + weights['favorites']
                        + weights['macd_buy_rate']
                )
            )

            conclusion = f'fundamental: {fundamental_rate}\n{fundamental_conclusion}\n\nprice: {price_prediction_rate}\n{price_prediction_conclusion}\n\nnews: {news_rate}\n{news_conclusion}\n\nmacd: {macd_rate}\n{macd_conclusion}'

            return {'rate': calc_rate / 100, 'conclusion': conclusion}
        except Exception as e:
            print('ERROR calculate_total_buy_rate', e)
    return {}


def calculate_total_sell_rate(
    invest_rate: int = None,
    invest_rate_conclusion: str = None,
    price_prediction_rate: int = None,
    price_prediction_conclusion: str = None,
    macd_rate: int = None,
    macd_conclusion: str = None,
):
    if invest_rate or price_prediction_rate:
        try:
            weights = {
                'invest_rate': 3,
                'macd_sell_rate': 2,
                'price_prediction_rate': 1,
            }
            calc_rate = int(
                (
                        (invest_rate or 0) * weights['invest_rate']
                        + (price_prediction_rate or 0) * weights['price_prediction_rate']
                        + (macd_rate or 0) * weights['macd_sell_rate']
                )
                / (weights['invest_rate'] + weights['price_prediction_rate'] + weights['macd_sell_rate'])
            )

            conclusion = f'invest: {invest_rate}\n{invest_rate_conclusion}\n\nprice: {price_prediction_rate}\n{price_prediction_conclusion}\n\nmacd: {macd_rate}\n{macd_conclusion}'

            return {'rate': calc_rate / 100, 'conclusion': conclusion}
        except Exception as e:
            print('ERROR calculate_total_sell_rate', e)
    return {}


def get_total_buy_rate(instrument_uid: str) -> dict:
    final_rate = 0
    macd_rated = agent.macd.macd_buy_rate(instrument_uid=instrument_uid)
    rsi_rated = agent.rsi.rsi_buy_rate(instrument_uid=instrument_uid)
    tech_rated = agent.price.price_buy_rate(instrument_uid=instrument_uid)

    weights = {
        'macd': 1,
        'rsi': 1,
        'tech': 1,
    }

    if macd_rated and rsi_rated and tech_rated:
        macd_rated_value = macd_rated.get('rate', None)
        rsi_rated_value = rsi_rated.get('rate', None)
        tech_rated_value = tech_rated.get('rate', None)

        if (
                macd_rated_value is not None
                and rsi_rated_value is not None
                and tech_rated_value is not None
        ):
            final_rate = (
                    (macd_rated_value * weights['macd'])
                    + (rsi_rated_value * weights['rsi'])
                    + (tech_rated_value * weights['tech'])
            ) / (
                    weights['macd']
                    + weights['rsi']
                    + weights['tech']
            )

    return {
        'rate': final_rate,
    }


def get_total_sell_rate(instrument_uid: str) -> dict:
    final_rate = 0
    macd_rated = agent.macd.macd_sell_rate(instrument_uid=instrument_uid)
    rsi_rated = agent.rsi.rsi_sell_rate(instrument_uid=instrument_uid)
    tech_rated = agent.price.price_sell_rate(instrument_uid=instrument_uid)

    weights = {
        'macd': 1,
        'rsi': 1,
        'tech': 1,
    }

    if macd_rated and rsi_rated and tech_rated:
        macd_rated_value = macd_rated.get('rate', None)
        rsi_rated_value = rsi_rated.get('rate', None)
        tech_rated_value = tech_rated.get('rate', None)

        if (
                macd_rated_value is not None
                and rsi_rated_value is not None
                and tech_rated_value is not None
        ):
            final_rate = (
                    (macd_rated_value * weights['macd'])
                    + (rsi_rated_value * weights['rsi'])
                    + (tech_rated_value * weights['tech'])
            ) / (
                    weights['macd']
                    + weights['rsi']
                    + weights['tech']
            )

    return {
        'rate': final_rate,
    }
