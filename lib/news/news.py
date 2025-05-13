import datetime

from lib.db_2 import news_db
from lib import instruments, yandex, cache, serializer, utils, logger
from lib.news import news_rate_v1


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


@cache.ttl_cache(ttl=3600 * 24 * 14, skip_empty=True)
def get_news_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime
) -> list[news_db.News]:
    keywords = get_keywords_by_instrument_uid(instrument_uid=instrument_uid)

    return news_db.get_news_by_date_keywords_fts(
        start_date=start_date,
        end_date=end_date,
        keywords=keywords
    ) or []


@cache.ttl_cache(ttl=3600 * 24 * 365, skip_empty=True)
def get_keywords_by_instrument_uid(instrument_uid: str) -> list[str]:
    i = instruments.get_instrument_by_uid(instrument_uid)
    response = []

    for word in yandex.get_keywords(legal_name=i.name):
        if word not in response:
            response.append(word)

    return response
