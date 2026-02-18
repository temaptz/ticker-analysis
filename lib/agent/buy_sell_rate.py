from lib import agent


def get_total_buy_rate(instrument_uid: str) -> dict:
    final_rate = 0
    macd_rated_value = None
    rsi_rated_value =None
    tech_rated_value =  None
    macd_rated = agent.macd.macd_buy_rate(instrument_uid=instrument_uid)
    rsi_rated = agent.rsi.rsi_buy_rate(instrument_uid=instrument_uid)
    tech_rated = agent.tech.get_tech_buy_rate(instrument_uid=instrument_uid)

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
        'debug': {
            'macd': macd_rated_value,
            'rsi': rsi_rated_value,
            'tech': tech_rated_value,
        },
    }


def get_total_sell_rate(instrument_uid: str) -> dict:
    final_rate = 0
    macd_rated_value = None
    rsi_rated_value = None
    tech_rated_value = None
    macd_rated = agent.macd.macd_sell_rate(instrument_uid=instrument_uid)
    rsi_rated = agent.rsi.rsi_sell_rate(instrument_uid=instrument_uid)
    tech_rated = agent.tech.get_tech_sell_rate(instrument_uid=instrument_uid)

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
        'debug': {
            'macd': macd_rated_value,
            'rsi': rsi_rated_value,
            'tech': tech_rated_value,
        },
    }
