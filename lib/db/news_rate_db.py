import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive


def init_table():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "News_rate" 
    (
    "news_uid" TEXT,
    "instrument_uid" TEXT,
    "rate" TINYINT,
    "date" timestamp
    )
    ''')
    connection.commit()
    connection.close()


def get_rate_by_uid(news_uid: str, instrument_uid: str):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM News_rate WHERE news_uid = ? AND instrument_uid = ?', (news_uid, instrument_uid))
    news = cursor.fetchall()
    connection.close()

    return news


def insert_rate(news_uid: str, instrument_uid: str, rate: int):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO News_rate (news_uid, instrument_uid, rate, date) VALUES (?, ?, ?, ?)',
        (news_uid, instrument_uid, rate, datetime.datetime.now())
    )
    connection.commit()
    connection.close()
