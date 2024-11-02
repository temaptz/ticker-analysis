import datetime
import pickle
import sqlite3
import const
from utils import get_db_path


def init_table():
    connection = sqlite3.connect(const.DB_PATH)
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
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Learning')
    forecasts = cursor.fetchall()
    connection.close()

    return forecasts


def get_learning_by_uid_date(uid: str, date: datetime.datetime):
    connection = sqlite3.connect(get_db_path(const.DB_PATH))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Learning WHERE uid = ? AND date = ?', (uid, date))
    forecasts = cursor.fetchall()
    connection.close()

    return forecasts


def insert_learning(uid: str, date: datetime.datetime, json: str):
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Learning (uid, date, json) VALUES (?, ?, ?)', (uid, date, json))
    connection.commit()
    connection.close()
