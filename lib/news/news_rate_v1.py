import datetime

from django.db.models.expressions import result

import const
from lib.db_2 import news_db
from lib import instruments, yandex, cache, counter, docker, serializer, utils, logger, types_util


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
        news_list: list[news_db.News],
        keywords: list[str],
) -> dict:
    news_ids_list = [n.news_uid for n in news_list or []]

    response: dict = {
        'list': [],
        'keywords': keywords,
        'total_absolute': get_news_rate_absolute(
            news_uid_list=news_ids_list,
            instrument_uid=instrument_uid,
        ),
        'total_percent': get_news_rate(
            news_uid_list=news_ids_list,
            instrument_uid=instrument_uid,
        )
    }

    for n in news_list or []:
        response['list'].append({
            'news_uid': n.news_uid,
            'title': n.title,
            'text': n.text,
            'date': n.date,
            'source': n.source_name,
            'rate_absolute': get_news_rate_absolute(
                news_uid_list=[n.news_uid],
                instrument_uid=instrument_uid,
            ),
            'rate_percent': get_news_rate(
                news_uid_list=[n.news_uid],
                instrument_uid=instrument_uid,
            ),
        })

    return response


def get_news_rate(
        news_uid_list: list[str],
        instrument_uid: str,
) -> types_util.NewsRate or None:
    abs_rate = get_news_rate_absolute(news_uid_list=news_uid_list, instrument_uid=instrument_uid)

    if abs_rate:
        total_sum = abs_rate.positive_total + abs_rate.negative_total + abs_rate.neutral_total

        if total_sum > 0:
            rate = types_util.NewsRate(0, 0, 0)

            rate.positive_percent = utils.round_float(
                num=(abs_rate.positive_total / total_sum * 100),
                decimals=5,
            )

            rate.negative_percent = utils.round_float(
                num=(abs_rate.negative_total / total_sum * 100),
                decimals=5,
            )

            rate.neutral_percent = utils.round_float(
                num=(abs_rate.neutral_total / total_sum * 100),
                decimals=5,
            )

            return rate

    return None


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_news_rate_absolute(
        news_uid_list: list[str],
        instrument_uid: str,
) -> types_util.NewsRateAbsoluteYandex or None:
    news = []
    for news_uid in news_uid_list:
        n = news_db.get_news_by_uid(news_uid=news_uid)

        if n:
            news.append(n)

    instrument = instruments.get_instrument_by_uid(uid=instrument_uid)

    if news and len(news) > 0 and instrument:
        subject_name = yandex.get_human_name(legal_name=instrument.name)
        total_rate_positive = 0
        total_rate_negative = 0
        total_rate_neutral = 0

        for n in news:
            c = yandex.get_text_classify_db_cache(
                title=n.title,
                text=n.text,
                subject_name=subject_name,
            )

            if c:
                abs_rate: types_util.NewsRateAbsoluteYandex = yandex.get_news_rate_absolute_by_ya_classify(classify=c)

                if abs_rate:
                    total_rate_positive += abs_rate.positive_total
                    total_rate_negative += abs_rate.negative_total
                    total_rate_neutral += abs_rate.neutral_total

        if total_rate_positive > 0 or total_rate_negative > 0 or total_rate_neutral > 0:
            return types_util.NewsRateAbsoluteYandex(
                positive_total=total_rate_positive,
                negative_total=total_rate_negative,
                neutral_total=total_rate_neutral,
            )

    return None
