import datetime

from django.db.models.expressions import result

import const
from lib.db_2 import news_db
from lib import instruments, yandex, cache, counter, docker, serializer, utils, logger, types


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


def get_sorted_rated_news_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        is_with_content=False
):
    result = {
        'sources': {
            'RBC': NewsSourceRated(),
            'FINAM': NewsSourceRated(),
            'RG': NewsSourceRated()
        },
        'keywords': get_keywords_by_instrument_uid(instrument_uid),
        'total': NewsSourceRated(),
    }

    news = get_news_by_instrument_uid(
        uid=instrument_uid,
        start_date=start_date,
        end_date=end_date
    )

    for n in news or []:
        news_uid = n.news_uid
        title = n.title
        text = n.text
        date = n.date
        source = n.source_name
        result_source: NewsSourceRated = result['sources'][source]
        rate: types.NewsRate = get_news_rate(news_uid_list=[news_uid], instrument_uid=instrument_uid)

        if is_with_content:
            result_source.content.append({
                'uid': news_uid,
                'title': title,
                'text': text,
                'date': date,
                'rate': rate,
            })

        if rate:
            result_source.positive_sum_percent += rate.positive_percent
            result_source.negative_sum_percent += rate.negative_percent
            result_source.neutral_sum_percent += rate.neutral_percent

            result['total'].positive_sum_percent += rate.positive_percent
            result['total'].negative_sum_percent += rate.negative_percent
            result['total'].neutral_sum_percent += rate.neutral_percent

        result_source.total_count += 1
        result['total'].total_count += 1

    for source_name in result['sources']:
        source: NewsSourceRated = result['sources'][source_name]

        if source.total_count > 0:
            source.positive_avg_percent = utils.round_float(
                num=source.positive_sum_percent / source.total_count,
                decimals=0,
            )
            source.negative_avg_percent = utils.round_float(
                num=source.negative_sum_percent / source.total_count,
                decimals=0,
            )
            source.neutral_avg_percent = utils.round_float(
                num=source.neutral_sum_percent / source.total_count,
                decimals=0,
            )

    if result['total'].total_count > 0:
        result['total'].positive_avg_percent = utils.round_float(
            num=result['total'].positive_sum_percent / result['total'].total_count,
            decimals=0,
        )

        result['total'].negative_avg_percent = utils.round_float(
            num=result['total'].negative_sum_percent / result['total'].total_count,
            decimals=0,
        )

        result['total'].neutral_avg_percent = (
                100 - result['total'].positive_avg_percent - result['total'].negative_avg_percent
        )

    return result


@logger.error_logger
def get_rated_news_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
):
    news = get_news_by_instrument_uid(
        uid=instrument_uid,
        start_date=start_date,
        end_date=end_date
    )
    news_ids_list = [n.news_uid for n in news or []]

    response = {
        'list': [],
        'keywords': get_keywords_by_instrument_uid(instrument_uid),
        'total_absolute': get_news_rate_absolute(
            news_uid_list=news_ids_list,
            instrument_uid=instrument_uid,
        ),
        'total_percent': get_news_rate(
            news_uid_list=news_ids_list,
            instrument_uid=instrument_uid,
        )
    }

    for n in news or []:
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


def get_news_rate_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
):
    response = None
    news = get_news_by_instrument_uid(
        uid=instrument_uid,
        start_date=start_date,
        end_date=end_date
    )
    news_uid_list = [n.news_uid for n in news]

    yandex_absolute_rate: types.NewsRateAbsoluteYandex = get_news_rate_absolute(
        news_uid_list=news_uid_list,
        instrument_uid=instrument_uid,
    )

    yandex_percent_rate: types.NewsRateAbsoluteYandex = get_news_rate(
        news_uid_list=news_uid_list,
        instrument_uid=instrument_uid,
    )

    if yandex_absolute_rate or yandex_percent_rate:
        response = {
            'yandex_absolute': yandex_absolute_rate,
            'yandex_percent': yandex_percent_rate,
            'keywords': get_keywords_by_instrument_uid(instrument_uid),
            'start_date': start_date,
            'end_date': end_date,
        }

    return response


def get_news_rate(
        news_uid_list: [str],
        instrument_uid: str,
) -> types.NewsRate or None:
    abs_rate = get_news_rate_absolute(news_uid_list=news_uid_list, instrument_uid=instrument_uid)

    if abs_rate:
        total_sum = abs_rate.positive_total + abs_rate.negative_total + abs_rate.neutral_total

        if total_sum > 0:
            rate = types.NewsRate(0, 0, 0)

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


@cache.ttl_cache(ttl=3600)
def get_news_rate_absolute(
        news_uid_list: [str],
        instrument_uid: str,
) -> types.NewsRateAbsoluteYandex or None:
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
                abs_rate: types.NewsRateAbsoluteYandex = yandex.get_news_rate_absolute_by_ya_classify(classify=c)

                if abs_rate:
                    total_rate_positive += abs_rate.positive_total
                    total_rate_negative += abs_rate.negative_total
                    total_rate_neutral += abs_rate.neutral_total

        if total_rate_positive > 0 or total_rate_negative > 0 or total_rate_neutral > 0:
            return types.NewsRateAbsoluteYandex(
                positive_total=total_rate_positive,
                negative_total=total_rate_negative,
                neutral_total=total_rate_neutral,
            )

    return None


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
