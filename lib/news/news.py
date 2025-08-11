import datetime

from tinkoff.invest import CandleInterval

from lib.db_2 import news_db
from lib import instruments, yandex, cache, serializer, utils, logger, learn, types_util, date_utils
from lib.news import news_rate_v1, news_rate_v2


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
        'total_absolute': news_rate_v1.get_news_rate_absolute(
            news_uid_list=news_ids_list,
            instrument_uid=instrument_uid,
        ),
        'total_percent': news_rate_v1.get_news_rate(
            news_uid_list=news_ids_list,
            instrument_uid=instrument_uid,
        ),
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
            'rate_absolute': news_rate_v1.get_news_rate_absolute(
                news_uid_list=[n.news_uid],
                instrument_uid=instrument_uid,
            ),
            'rate_percent': news_rate_v1.get_news_rate(
                news_uid_list=[n.news_uid],
                instrument_uid=instrument_uid,
            ),
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

    for date in date_utils.get_dates_interval_list(
        date_from=start_date,
        date_to=end_date,
        interval_seconds=date_utils.get_interval_sec_by_candle(interval=interval)
    ):
        news_list = get_news_by_instrument_uid(
            instrument_uid=instrument_uid,
            start_date=date_utils.get_day_start(date),
            end_date=date_utils.get_day_end(date),
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
        start_date=datetime.datetime.now() - datetime.timedelta(days=30),
        end_date=datetime.datetime.now(),
    ):
        if news_rate_v2.get_news_rate_db(
            news_uid=n.news_uid,
            instrument_uid=instrument_uid,
        ) is None:
            return n

    return None
