import datetime
from lib import logger, news, date_utils

NEWS_CANDLES_COUNT = 7

def get_news_buy_rate(instrument_uid: str):
    final_rate = 0
    influence_score = None

    try:
        influence_score = get_news_influence_score(instrument_uid=instrument_uid)

        if influence_score > 0:
            final_rate = 1
    except Exception as e:
        logger.log_error(method_name='get_news_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'influence_score': influence_score,
            'news_count': get_news_count(instrument_uid=instrument_uid),
            'from_date': get_news_period()[0],
            'to_date': get_news_period()[1],
        },
    }


def get_news_sell_rate(instrument_uid: str):
    final_rate = 0
    influence_score = None

    try:
        influence_score = get_news_influence_score(instrument_uid=instrument_uid)

        if influence_score < 0:
            final_rate = 1
    except Exception as e:
        logger.log_error(method_name='get_news_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'influence_score': influence_score,
            'news_count': get_news_count(instrument_uid=instrument_uid),
            'from_date': get_news_period()[0],
            'to_date': get_news_period()[1],
        },
    }


def get_news_influence_score(instrument_uid: str) -> float:
    try:
        period = get_news_period()

        return news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=period[0],
            end_date=period[1],
        )

    except Exception as e:
        logger.log_error(method_name='get_news_influence_score', error=e, is_telegram_send=False)
    return 0

def get_news_count(instrument_uid: str) -> int:
    try:
        period = get_news_period()
        news_list = news.news.get_news_by_instrument_uid(
            instrument_uid=instrument_uid,
            start_date=period[0],
            end_date=period[1],
        )

        return len(news_list)

    except Exception as e:
        logger.log_error(method_name='get_news_count', error=e, is_telegram_send=False)
    return 0


def get_news_period() -> (datetime.datetime, datetime.datetime):
    end_date = date_utils.get_day_prediction_time(date=datetime.datetime.now(datetime.timezone.utc))
    start_date = end_date - datetime.timedelta(days=14)
    return start_date, end_date
