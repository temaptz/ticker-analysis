import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive


def init_table():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "News" 
    (
    "uid" TEXT,
    "title" TEXT,
    "text" TEXT,
    "date" timestamp,
    "source_name" TEXT
    )
    ''')
    connection.commit()
    connection.close()


def get_news():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM News')
    news = cursor.fetchall()
    connection.close()

    return news


def get_news_by_uid(uid: str):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM News WHERE uid = ?', (uid,))
    news = cursor.fetchall()
    connection.close()

    return news


def insert_news(uid: str, title: str, text: str, date: datetime.datetime, source_name):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO News (uid, title, text, date, source_name) VALUES (?, ?, ?, ?, ?)',
        (uid, title, text, date, source_name)
    )
    connection.commit()
    connection.close()
