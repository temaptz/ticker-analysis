import datetime

from lib.db import news_db
from lib.news_parsers import (rbc, rg, finam)
from lib import telegram


def get_news_by_instrument_uid():
    start_date = datetime.datetime.now() - datetime.timedelta(days=30)
    end_date = datetime.datetime.now()

    news = news_db.get_news_by_source_date_keywords(
        start_date=start_date,
        end_date=end_date,
        keywords=['озон', 'ozon']
    )

    print(start_date)
    print(end_date)

    for n in news:
        print(n)

    print(len(news))
