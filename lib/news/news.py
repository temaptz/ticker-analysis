import datetime

from t_tech.invest import CandleInterval

from lib.db_2 import news_db
from lib import instruments, yandex, cache, serializer, utils, logger, learn, types_util, date_utils
from lib.news import news_rate_v1, news_rate_v2

news_beginning_date = datetime.datetime(year=2025, month=2, day=17) # datetime.datetime(year=2025, month=1, day=29)  # Самые первые новости


class NewsSourceRated:
    def __init__(self):
        self.positive_sum_percent = 0
        self.positive_avg_percent = 0
        self.negative_sum_percent = 0
        self.negative_avg_percent = 0
        self.neutral_sum_percent = 0
        self.neutral_avg_percent = 0
        self.total_count = 0
        self.content = list()


@logger.error_logger
def get_rated_news_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
):
    news_list = get_news_by_instrument_uid(
        instrument_uid=instrument_uid,
        start_date=start_date,
        end_date=end_date,
    )
    news_ids_list = [n.news_uid for n in news_list or []]
    keywords = instruments.get_instrument_keywords(uid=instrument_uid)
    response: dict = {
        'list': [],
        'keywords': keywords,
        'rate_v2': {
            'influence_score': utils.round_float(news_rate_v2.get_news_total_influence_score(
                instrument_uid=instrument_uid,
                news_ids=news_ids_list,
            ))
        },
        'start_date': start_date,
        'end_date': end_date,
    }

    for n in news_list or []:
        response['list'].append({
            'news_uid': n.news_uid,
            'title': n.title,
            'text': n.text,
            'date': n.date,
            'source': n.source_name,
            'rate_v2': news_rate_v2.get_news_rate_db(
                news_uid=n.news_uid,
                instrument_uid=instrument_uid,
            ),
        })

    return response


@logger.error_logger
def get_rated_news_graph(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        interval: CandleInterval,
):
    response = []
    interval_sec = date_utils.get_interval_sec_by_candle(interval=interval)

    for date in date_utils.get_dates_interval_list(
        date_from=start_date,
        date_to=end_date,
        interval_seconds=interval_sec
    ):
        news_list = get_news_by_instrument_uid(
            instrument_uid=instrument_uid,
            start_date=date_utils.get_day_start(date),
            end_date=date_utils.get_day_end(date + datetime.timedelta(seconds=interval_sec)),
        )
        news_ids_list = [n.news_uid for n in news_list or []]
        influence_score = news_rate_v2.get_news_total_influence_score(
            instrument_uid=instrument_uid,
            news_ids=news_ids_list,
        )

        if influence_score:
            response.append({
                'date': date,
                'influence_score': influence_score,
            })

    return response


@logger.error_logger
def get_influence_score(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
) -> float:
    influence_score = 0
    news_list = get_news_by_instrument_uid(
        instrument_uid=instrument_uid,
        start_date=start_date,
        end_date=end_date,
    )
    if influence_score := utils.round_float(news_rate_v2.get_news_total_influence_score(
        instrument_uid=instrument_uid,
        news_ids=[n.news_uid for n in news_list or []],
    )):
        return influence_score

    return influence_score


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_news(
        start_date: datetime.datetime,
        end_date: datetime.datetime
) -> list[news_db.News]:
    result = []

    for i in instruments.get_instruments_white_list():
        result.extend(get_news_by_instrument_uid(
            instrument_uid=i.uid,
            start_date=start_date,
            end_date=end_date,
        ) or [])

    return result


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_news_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime
) -> list[news_db.News]:
    keywords = instruments.get_instrument_keywords(uid=instrument_uid)

    return news_db.get_news_by_date_keywords_fts(
        start_date=start_date,
        end_date=end_date,
        keywords=keywords
    ) or []


def get_last_unrated_news_by_instrument_uid(
        instrument_uid: str,
) -> news_db.News or None:
    for n in get_news_by_instrument_uid(
        instrument_uid=instrument_uid,
        start_date=news_beginning_date,
        end_date=datetime.datetime.now(),
    ):
        if news_rate_v2.get_news_rate_db(
            news_uid=n.news_uid,
            instrument_uid=instrument_uid,
        ) is None:
            return n

    return None
