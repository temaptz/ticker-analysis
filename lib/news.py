import datetime
from tinkoff.invest import (
    Client,
    constants,
    GetAccountsResponse,
    PositionsResponse,
    Operation,
    OperationState
)
from const import TOKEN

from lib.db import news_db
from lib.news_parsers import (rbc, rg, finam)
from lib import instruments, yandex, cache


def get_sorted_news_by_instrument_uid_by_source(
        uid: str,
        # start_date: datetime.datetime,
        # end_date: datetime.datetime
):
    start_date = datetime.datetime.now() - datetime.timedelta(days=3)
    end_date = datetime.datetime.now()

    result = {
        'RBC': {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'total': 0,
        },
        'FINAM': {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'total': 0,
        },
        'RG': {
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'total': 0,
        }
    }

    news = get_news_by_instrument_uid(
        uid=uid,
        start_date=start_date,
        end_date=end_date
    )
    instrument = instruments.get_instrument_by_uid(uid)

    for n in news:
        title = n[1]
        text = n[2]
        source = n[4]
        rate = get_news_rate(title=title, text=text, subject_name=yandex.get_human_name(instrument.name))

        if rate == 1:
            result[source]['positive'] += 1
        elif rate == -1:
            result[source]['negative'] += 1
        elif rate == 0:
            result[source]['neutral'] += 1

        result[source]['total'] += 1

    print(result)

    return result


@cache.ttl_cache()
def get_news_rate(
        title: str,
        text: str,
        subject_name: str
) -> int:
    return yandex.get_text_classify(title=title, text=text, subject_name=subject_name)


@cache.ttl_cache()
def get_news_by_instrument_uid(
        uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime
):
    return news_db.get_news_by_source_date_keywords(
        start_date=start_date,
        end_date=end_date,
        keywords=get_keywords_by_instrument_uid(uid)
    )


@cache.ttl_cache()
def get_keywords_by_instrument_uid(uid: str) -> list[str]:
    result = list()
    i = instruments.get_instrument_by_uid(uid)
    result.append(i.ticker.lower())
    result.append(i.name.lower())

    gpt_resp = yandex.get_gpt_text(
        'Как в СМИ называют эту компанию, однозначно и понятно для большинства: "'
        + i.name + '"? '
        + 'Составь список из одного или нескольких вариантов. '
        + 'В качестве разделителя используй точку с запятой. '
    ).strip('.')

    for word in [s.strip().lower() for s in gpt_resp.split(';')]:
        if word not in result:
            result.append(word)

    return result
