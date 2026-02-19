from lib import agent, db_2, logger


def get_total_buy_rate(instrument_uid: str) -> dict:
    final_rate = 0
    macd_rated_value = None
    rsi_rated_value =None
    tech_rated_value =  None
    news_rated_value = None
    fundamental_rated_value = None
    volume_rated_value = None
    profit_rated_value = None
    macd_rated = agent.macd.macd_buy_rate(instrument_uid=instrument_uid)
    rsi_rated = agent.rsi.rsi_buy_rate(instrument_uid=instrument_uid)
    tech_rated = agent.tech.get_tech_buy_rate(instrument_uid=instrument_uid)
    news_rated = agent.news.get_news_buy_rate(instrument_uid=instrument_uid)
    fundamental_rated = agent.fundamental.get_fundamental_buy_rate(instrument_uid=instrument_uid)
    volume_rated = agent.volume.get_volume_buy_rate(instrument_uid=instrument_uid)
    profit_rated = agent.profit.get_profit_buy_rate(instrument_uid=instrument_uid)

    weights = get_buy_weights()

    if macd_rated and rsi_rated and tech_rated and news_rated and fundamental_rated and volume_rated and profit_rated:
        macd_rated_value = macd_rated.get('rate', None)
        rsi_rated_value = rsi_rated.get('rate', None)
        tech_rated_value = tech_rated.get('rate', None)
        news_rated_value = news_rated.get('rate', None)
        fundamental_rated_value = fundamental_rated.get('rate', None)
        volume_rated_value = volume_rated.get('rate', None)
        profit_rated_value = profit_rated.get('rate', None)

        if (
                macd_rated_value is not None
                and rsi_rated_value is not None
                and tech_rated_value is not None
                and news_rated_value is not None
                and fundamental_rated_value is not None
                and volume_rated_value is not None
                and profit_rated_value is not None
        ):
            final_rate = (
                    (macd_rated_value * weights['macd'])
                    + (rsi_rated_value * weights['rsi'])
                    + (tech_rated_value * weights['tech'])
                    + (news_rated_value * weights['news'])
                    + (fundamental_rated_value * weights['fundamental'])
                    + (volume_rated_value * weights['volume'])
                    + (profit_rated_value * weights['profit'])
            ) / (
                    weights['macd']
                    + weights['rsi']
                    + weights['tech']
                    + weights['news']
                    + weights['fundamental']
                    + weights['volume']
                    + weights['profit']
            )

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'macd': macd_rated_value,
            'rsi': rsi_rated_value,
            'tech': tech_rated_value,
            'news': news_rated_value,
            'fundamental': fundamental_rated_value,
            'volume': volume_rated_value,
            'profit': profit_rated_value,
        },
    }


def get_total_sell_rate(instrument_uid: str) -> dict:
    final_rate = 0
    macd_rated_value = None
    rsi_rated_value = None
    tech_rated_value = None
    news_rated_value = None
    fundamental_rated_value = None
    volume_rated_value = None
    profit_rated_value = None
    macd_rated = agent.macd.macd_sell_rate(instrument_uid=instrument_uid)
    rsi_rated = agent.rsi.rsi_sell_rate(instrument_uid=instrument_uid)
    tech_rated = agent.tech.get_tech_sell_rate(instrument_uid=instrument_uid)
    news_rated = agent.news.get_news_sell_rate(instrument_uid=instrument_uid)
    fundamental_rated = agent.fundamental.get_fundamental_sell_rate(instrument_uid=instrument_uid)
    volume_rated = agent.volume.get_volume_sell_rate(instrument_uid=instrument_uid)
    profit_rated = agent.profit.get_profit_sell_rate(instrument_uid=instrument_uid)

    weights = get_sell_weights()

    if macd_rated and rsi_rated and tech_rated and news_rated and fundamental_rated and volume_rated and profit_rated:
        macd_rated_value = macd_rated.get('rate', None)
        rsi_rated_value = rsi_rated.get('rate', None)
        tech_rated_value = tech_rated.get('rate', None)
        news_rated_value = news_rated.get('rate', None)
        fundamental_rated_value = fundamental_rated.get('rate', None)
        volume_rated_value = volume_rated.get('rate', None)
        profit_rated_value = profit_rated.get('rate', None)

        if (
                macd_rated_value is not None
                and rsi_rated_value is not None
                and tech_rated_value is not None
                and news_rated_value is not None
                and fundamental_rated_value is not None
                and volume_rated_value is not None
                and profit_rated_value is not None
        ):
            final_rate = (
                    (macd_rated_value * weights['macd'])
                    + (rsi_rated_value * weights['rsi'])
                    + (tech_rated_value * weights['tech'])
                    + (news_rated_value * weights['news'])
                    + (fundamental_rated_value * weights['fundamental'])
                    + (volume_rated_value * weights['volume'])
                    + (profit_rated_value * weights['profit'])
            ) / (
                    weights['macd']
                    + weights['rsi']
                    + weights['tech']
                    + weights['news']
                    + weights['fundamental']
                    + weights['volume']
                    + weights['profit']
            )

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'macd': macd_rated_value,
            'rsi': rsi_rated_value,
            'tech': tech_rated_value,
            'news': news_rated_value,
            'fundamental': fundamental_rated_value,
            'volume': volume_rated_value,
            'profit': profit_rated_value,
        },
    }


def get_buy_weights() -> dict:
    weights = {
        'macd': get_weight_db(name='buy_macd') or 0,
        'rsi': get_weight_db(name='buy_rsi') or 0,
        'tech': get_weight_db(name='buy_tech') or 0,
        'news': get_weight_db(name='buy_news') or 0,
        'fundamental': get_weight_db(name='buy_fundamental') or 0,
        'volume': get_weight_db(name='buy_volume') or 0,
        'profit': get_weight_db(name='buy_profit') or 0,
    }

    return weights


def get_sell_weights() -> dict:
    weights = {
        'macd': get_weight_db(name='sell_macd') or 0,
        'rsi': get_weight_db(name='sell_rsi') or 0,
        'tech': get_weight_db(name='sell_tech') or 0,
        'news': get_weight_db(name='sell_news') or 0,
        'fundamental': get_weight_db(name='sell_fundamental') or 0,
        'volume': get_weight_db(name='sell_volume') or 0,
        'profit': get_weight_db(name='sell_profit') or 0,
    }

    return weights


def get_weight_db(name: str) -> float or None:
    try:
        if weight_db := db_2.weights.get_weight(name=name):
            if weight_db.value is not None:
                return float(weight_db.value)
    except Exception as e:
        logger.log_error(method_name='get_weight_db', error=e, is_telegram_send=False)
    return None


def set_weight_db(name: str, value: float) -> None:
    try:
        db_2.weights.upset_weight(
            name=name,
            value=value,
        )
    except Exception as e:
        logger.log_error(method_name='set_weight_db', error=e, is_telegram_send=False)
    return None
