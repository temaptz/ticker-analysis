import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive
from lib import types, serializer

table_name = 'News_rate_cache'


def init_table():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS 
    "{table_name}" 
    (
    "news_uid" TEXT,
    "instrument_uid" TEXT,
    "rate" TEXT,
    "date" timestamp
    )
    ''')
    connection.commit()
    connection.close()


def get_all():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'SELECT * FROM {table_name}')
    resp = cursor.fetchall()
    connection.close()
    return resp


def get_rate_by_uid(news_uid: str, instrument_uid: str) -> types.NewsRate or None:
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'SELECT * FROM {table_name} WHERE news_uid = ? AND instrument_uid = ?', (news_uid, instrument_uid))
    resp = cursor.fetchone()
    connection.close()

    if resp and len(resp) and resp[2]:
        deserialized_dict = serializer.from_json(resp[2])

        return types.NewsRate(
            positive_percent=deserialized_dict.get('positive_percent', 0),
            negative_percent=deserialized_dict.get('negative_percent', 0),
            neutral_percent=deserialized_dict.get('neutral_percent', 0),
        )

    return None


def insert_rate(news_uid: str, instrument_uid: str, rate: types.NewsRate):
    rate_json = serializer.to_json(rate)

    if rate_json:
        connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
        cursor = connection.cursor()
        cursor.execute(
            f'INSERT INTO {table_name} (news_uid, instrument_uid, rate, date) VALUES (?, ?, ?, ?)',
            (news_uid, instrument_uid, rate_json, datetime.datetime.now())
        )
        connection.commit()
        connection.close()
