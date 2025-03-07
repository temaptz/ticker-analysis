import datetime

import const
from lib.db import news_db, news_rate_db
from lib import instruments, yandex, cache, counter, docker, serializer, utils


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


def get_sorted_news_by_instrument_uid(
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
        'keywords': get_keywords_by_instrument_uid(instrument_uid)
    }

    news = get_news_by_instrument_uid(
        uid=instrument_uid,
        start_date=start_date,
        end_date=end_date
    )

    for n in news or []:
        news_uid = n[0]
        title = n[1]
        text = n[2]
        date = n[3]
        source = n[4]
        result_source: NewsSourceRated = result['sources'][source]
        rate: yandex.NewsRate = get_news_rate(news_uid=news_uid, instrument_uid=instrument_uid)

        print('NEWS RATED', serializer.get_dict_by_object_recursive(rate), title)

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
            result_source.total_count += 1

    for source_name in result['sources']:
        source: NewsSourceRated = result['sources'][source_name]
        source.positive_avg_percent = utils.round_float(
            num=source.positive_sum_percent / source.total_count,
            decimals=2,
        )
        source.negative_avg_percent = utils.round_float(
            num=source.negative_sum_percent / source.total_count,
            decimals=2,
        )
        source.neutral_avg_percent = utils.round_float(
            num=source.neutral_sum_percent / source.total_count,
            decimals=2,
        )

    return result


def get_news_rate(
        news_uid: str,
        instrument_uid: str,
) -> yandex.NewsRate or None:
    rate_saved_db = news_rate_db.get_rate_by_uid(news_uid=news_uid, instrument_uid=instrument_uid)

    if rate_saved_db:
        counter.increment(counter.Counters.NEWS_RATE_DB)
        return rate_saved_db

    elif not const.IS_NEWS_CLASSIFY_ENABLED:
        return 0
    elif not docker.is_prod():
        return 0
    else:
        # Тут уже запрос GPT
        news = news_db.get_news_by_uid(news_uid)
        instrument = instruments.get_instrument_by_uid(instrument_uid)

        if news and len(news) > 0 and news[0] and instrument:
            title = news[0][1]
            text = news[0][2]

            subject_name = yandex.get_human_name(instrument.name)
            gpt_rate = yandex.get_text_classify_3(
                title=title,
                text=text,
                subject_name=subject_name
            )

            if gpt_rate:
                news_rate_db.insert_rate(news_uid=news_uid, instrument_uid=instrument_uid, rate=gpt_rate)
                counter.increment(counter.Counters.NEWS_RATE_NEW)

                return gpt_rate

    return None


@cache.ttl_cache(ttl=3600 * 24 * 7)
def get_news_by_instrument_uid(
        uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime
):
    keywords = get_keywords_by_instrument_uid(uid)

    print('GET NEWS BY KEYWORDS', keywords)
    counter.increment(counter.Counters.NEWS_GET_COUNT)

    return news_db.get_news_by_date_keywords_fts(
        start_date=start_date,
        end_date=end_date,
        keywords=keywords
    )


@cache.ttl_cache(ttl=3600 * 24 * 365)
def get_keywords_by_instrument_uid(uid: str) -> list[str]:
    i = instruments.get_instrument_by_uid(uid)
    result = []

    for word in yandex.get_keywords(legal_name=i.name):
        if word not in result:
            result.append(word)

    return result


# def append_percent_result_source(
#         result_source: NewsSourceRated,
#         positive_percent=0,
#         negative_percent=0,
#         neutral_percent=0
# ):
#     result_source.total_count += 1
#
#     if positive_percent > 0:
#         result_source.neutral_avg_percent = result_source.neutral_avg_percent +