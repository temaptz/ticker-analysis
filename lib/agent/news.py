import datetime
from lib import logger, news, date_utils, cache
from t_tech.invest import CandleInterval
from t_tech.invest.schemas import IndicatorInterval

NEWS_CANDLES_COUNT = 7


def get_news_buy_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    influence_score = None
    date_from = _get_news_period(date=date)[0]
    date_to = _get_news_period(date=date)[1]

    try:
        influence_score = _get_news_influence_score(instrument_uid=instrument_uid, date=date)

        if influence_score is not None and influence_score > 0:
            final_rate = 1
    except Exception as e:
        logger.log_error(method_name='get_news_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'influence_score': influence_score,
            'news_count': _get_news_count(instrument_uid=instrument_uid, date=date),
            'from_date': date_from,
            'to_date': date_to,
            'graph': _get_news_graph(
                instrument_uid=instrument_uid,
                date_from=date_from,
                date_to=date_to,
            ),
        },
    }


def get_news_sell_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    influence_score = None
    date_from = _get_news_period(date=date)[0]
    date_to = _get_news_period(date=date)[1]

    try:
        influence_score = _get_news_influence_score(instrument_uid=instrument_uid, date=date)

        if influence_score is not None and influence_score < 0:
            final_rate = 1
    except Exception as e:
        logger.log_error(method_name='get_news_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'influence_score': influence_score,
            'news_count': _get_news_count(instrument_uid=instrument_uid, date=date),
            'from_date': date_from,
            'to_date': date_to,
            'graph': _get_news_graph(
                instrument_uid=instrument_uid,
                date_from=date_from,
                date_to=date_to,
            ),
        },
    }


@cache.ttl_cache(ttl=(3600 * 5))
def _get_news_influence_score(instrument_uid: str, date: datetime.datetime or None = None) -> float:
    try:
        period = _get_news_period(date=date)

        return news.news.get_influence_score(
            instrument_uid=instrument_uid,
            start_date=period[0],
            end_date=period[1],
        )

    except Exception as e:
        logger.log_error(method_name='get_news_influence_score', error=e, is_telegram_send=False)
    return 0


@cache.ttl_cache(ttl=(3600 * 5))
def _get_news_count(instrument_uid: str, date: datetime.datetime or None = None) -> int:
    try:
        period = _get_news_period(date=date)
        news_list = news.news.get_news_by_instrument_uid(
            instrument_uid=instrument_uid,
            start_date=period[0],
            end_date=period[1],
        )

        return len(news_list)

    except Exception as e:
        logger.log_error(method_name='get_news_count', error=e, is_telegram_send=False)
    return 0


def _get_news_period(date: datetime.datetime or None = None) -> (datetime.datetime, datetime.datetime):
    end_date = date or date_utils.get_day_prediction_time(date=datetime.datetime.now(datetime.timezone.utc))
    start_date = end_date - datetime.timedelta(days=14)
    return start_date, end_date


@cache.ttl_cache(ttl=(3600 * 5))
def _get_news_graph(instrument_uid: str, date_from: datetime.datetime, date_to: datetime.datetime):
    return [i.get('influence_score') for i in news.news.get_rated_news_graph(
        instrument_uid=instrument_uid,
        start_date=date_from,
        end_date=date_to,
        interval=CandleInterval.CANDLE_INTERVAL_DAY,
    )]
