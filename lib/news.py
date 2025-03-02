import datetime

import const
from lib.db import news_db, news_rate_db
from lib import instruments, yandex, cache, counter


class NewsSourceRated:
    def __init__(self):
        self.positive_count = 0
        self.positive_percent = 0
        self.negative_count = 0
        self.negative_percent = 0
        self.neutral_count = 0
        self.neutral_percent = 0
        self.total_count = 0

    def update_percents(self):
        if self.total_count > 0:
            self.positive_percent = round((self.positive_count / self.total_count * 100), 2)
            self.negative_percent = round((self.negative_count / self.total_count * 100), 2)
            self.neutral_percent = round((self.neutral_count / self.total_count * 100), 2)


def get_sorted_rated_news_content_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime
):
    result = {
        'sources': {
            'RBC': list(),
            'FINAM': list(),
            'RG': list(),
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
        rate = get_news_rate(news_uid=news_uid, instrument_uid=instrument_uid)

        result['sources'][source].append({
            'uid': news_uid,
            'title': title,
            'text': text,
            'date': date,
            'rate': rate,
        })

    return result


def get_sorted_news_count_by_instrument_uid(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime
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

    print('GOT NEWS', news and len(news))

    for n in news or []:
        news_uid = n[0]
        source = n[4]
        rate = get_news_rate(news_uid=news_uid, instrument_uid=instrument_uid)
        result_source: NewsSourceRated = result['sources'][source]

        print('NEWS RATED', rate, n)

        if rate == 1:
            result_source.positive_count += 1
        elif rate == -1:
            result_source.negative_count += 1
        elif rate == 0:
            result_source.neutral_count += 1

        result_source.total_count += 1
        result_source.update_percents()

    return result


def get_news_rate(
        news_uid: str,
        instrument_uid: str,
) -> int or None:
    print('CALL GET RATE')

    rate_saved_db = news_rate_db.get_rate_by_uid(news_uid=news_uid, instrument_uid=instrument_uid)

    if rate_saved_db and len(rate_saved_db) and rate_saved_db[0] and rate_saved_db[0][2] is not None:
        print('RATE FROM DB', rate_saved_db[0][2])
        counter.increment(counter.Counters.NEWS_RATE_DB)
        return rate_saved_db[0][2]

    elif not const.IS_NEWS_CLASSIFY_ENABLED:
        return 0
    else:
        news = news_db.get_news_by_uid(news_uid)
        instrument = instruments.get_instrument_by_uid(instrument_uid)

        if news and len(news) > 0 and news[0] and instrument:
            title = news[0][1]
            text = news[0][2]

            subject_name = yandex.get_human_name(instrument.name)
            gpt_rate = yandex.get_text_classify_2(
                title=title,
                text=text,
                subject_name=subject_name
            )

            if gpt_rate is not None:
                news_rate_db.insert_rate(news_uid=news_uid, instrument_uid=instrument_uid, rate=gpt_rate)

                print('RATE FROM GPT', gpt_rate)
                counter.increment(counter.Counters.NEWS_RATE_NEW)

                return gpt_rate

    print('RATE NONE')

    return None


@cache.ttl_cache()
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
