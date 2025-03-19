import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive


def init_table():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Learning" 
    (
    "uid" TEXT,
    "date" timestamp,
    "json" TEXT
    )
    ''')
    connection.commit()
    connection.close()


def get_learning():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Learning')
    forecasts = cursor.fetchall()
    connection.close()

    return forecasts


def get_learning_by_uid_date(uid: str, date: datetime.datetime):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Learning WHERE uid = ? AND date = ?', (uid, date))
    forecasts = cursor.fetchall()
    connection.close()

    return forecasts


def insert_learning(uid: str, date: datetime.datetime, json: str):
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Learning (uid, date, json) VALUES (?, ?, ?)', (uid, date, json))
    connection.commit()
    connection.close()


def get_record_count():
    """
    Функция возвращает количество записей в таблице Learning.
    Возвращаемое значение — целое число (int).
    """
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM Learning")
    count = cursor.fetchone()[0]
    connection.close()
    return count
