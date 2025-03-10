from lib.db import news_db, db_utils
from lib.news_parsers import (rbc, rg, finam)
from lib import telegram, types


def save_news():
    print('UPDATING NEWS')
    telegram.send_message('Начато сохранение новостей')

    saved_news_counter = 0

    saved_news_counter += save_news_from_source_to_db('RBC', rbc.get_news())
    saved_news_counter += save_news_from_source_to_db('RG', rg.get_news())
    saved_news_counter += save_news_from_source_to_db('FINAM', finam.get_news())

    print('TOTAL SAVED '+str(saved_news_counter)+' NEWS')
    telegram.send_message('Всего сохранено '+str(saved_news_counter)+' новостей')


def save_news_from_source_to_db(source_name: str, news: list):
    saved_news_counter = 0

    if len(news):
        print('GOT '+str(len(news))+' NEWS FROM '+source_name)

        news_batch: list[types.NewsDbRecord] = []

        for i in news:
            if len(news_db.get_news_by_uid(i[0])) == 0:
                record = types.NewsDbRecord(
                    uid=i[0],
                    title=i[1],
                    text=i[2],
                    date=i[3],
                    source_name=i[4],
                )

                news_batch.append(record)
                saved_news_counter += 1

        if len(news_batch) > 0:
            news_db.insert_news_batch(news_batch)
            db_utils.optimize_db()

    else:
        print('NO NEWS FROM '+source_name)

    print('SAVED '+str(saved_news_counter)+' NEW ITEMS FROM '+source_name)

    return saved_news_counter
