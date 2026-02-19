import datetime
from lib import logger, news, date_utils

NEWS_CANDLES_COUNT = 7

def get_news_buy_rate(instrument_uid: str):
    final_rate = 0

    try:
        if get_news_influence_score(instrument_uid=instrument_uid) > 0:
            final_rate = 1
    except Exception as e:
        logger.log_error(method_name='get_news_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'news_count': 0,
        },
    }


def get_news_sell_rate(instrument_uid: str):
    final_rate = 0

    try:
        if get_news_influence_score(instrument_uid=instrument_uid) < 0:
            final_rate = 1
    except Exception as e:
        logger.log_error(method_name='get_news_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'news_count': 0,
        },
    }


def get_news_influence_score(instrument_uid: str) -> float:
    try:
        end_date = date_utils.get_day_prediction_time(date=datetime.datetime.now(datetime.timezone.utc))
        start_date = end_date - datetime.timedelta(days=NEWS_CANDLES_COUNT)

        return news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=start_date,
            end_date=end_date,
        ) or 0
    except Exception as e:
        logger.log_error(method_name='get_news_influence_score', error=e, is_telegram_send=False)
    return 0
