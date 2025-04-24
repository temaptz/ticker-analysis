import datetime

from django.db.models.expressions import result

import const
from lib.db_2 import news_db
from lib import instruments, yandex, cache, counter, docker, serializer, utils, logger, types, news_rate_v1


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
    return news_rate_v1.get_rated_news_by_instrument_uid(
        instrument_uid=instrument_uid,
        news_list=get_news_by_instrument_uid(
            instrument_uid=instrument_uid,
            start_date=start_date,
            end_date=end_date,
        ),
        keywords=get_keywords_by_instrument_uid(instrument_uid=instrument_uid),
    )


def get_news_rate_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
):
    return news_rate_v1.get_news_rate_by_instrument_uid(
        instrument_uid=instrument_uid,
        start_date=start_date,
        end_date=end_date,
        news_list=get_news_by_instrument_uid(
            instrument_uid=instrument_uid,
            start_date=start_date,
            end_date=end_date,
        ),
        keywords=get_keywords_by_instrument_uid(instrument_uid=instrument_uid),
    )


@logger.error_logger
def get_news_by_instrument_uid(
        uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime
):
    start_date_beginning_day = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_end_day = start_date.replace(hour=23, minute=59, second=59, microsecond=999)
    cache_key = utils.get_md5(serializer.to_json({
        'method': 'get_news_by_instrument_uid',
        'uid': uid,
        'start_date': start_date_beginning_day,
        'end_date': end_date_end_day,
    }))
    cached = cache.cache_get(cache_key)

    if cached:
        return cached

    keywords = get_keywords_by_instrument_uid(uid)

    response = news_db.get_news_by_date_keywords_fts(
        start_date=start_date,
        end_date=end_date,
        keywords=keywords
    )

    if response:
        cache.cache_set(key=cache_key, value=response, ttl=3600*24*14)

    return response


@cache.ttl_cache(ttl=3600 * 24 * 365)
def get_keywords_by_instrument_uid(uid: str) -> list[str]:
    i = instruments.get_instrument_by_uid(uid)
    response = []

    for word in yandex.get_keywords(legal_name=i.name):
        if word not in response:
            response.append(word)

    return response
