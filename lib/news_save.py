from lib.db import news_db
from lib.news_parsers import (rbc, rg, finam)
from lib import telegram


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

        for i in news:
            if len(news_db.get_news_by_uid(i[0])) == 0:
                news_db.insert_news(i[0], i[1], i[2], i[3], i[4])
                saved_news_counter += 1
    else:
        print('NO NEWS FROM '+source_name)

    print('SAVED '+str(saved_news_counter)+' NEW ITEMS FROM '+source_name)

    return saved_news_counter
