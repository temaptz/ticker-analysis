import datetime
from lib import (
    docker,
    instruments,
    news,
    yandex,
)

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if True or docker.is_docker():
    for i in instruments.get_instruments_white_list():
        subject_name = yandex.get_human_name(legal_name=i.name)
        print(i.ticker, subject_name)

        news_list = news.news.get_news_by_instrument_uid(
            instrument_uid=i.uid,
            start_date=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=3),
            end_date=datetime.datetime.now(datetime.timezone.utc),
        ) or []

        print('NEWS LEN', len(news_list))

        for n in news_list:
            if len(n.text) < 500:
                rate = news.news_rate_v2.get_news_rate(
                    news_uid=[n.news_uid],
                    subject_name=subject_name,
                )
