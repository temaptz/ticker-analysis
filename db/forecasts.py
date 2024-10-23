import datetime
import pickle
import sqlite3

import const
from .utils import get_db_path


def init_table():
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Forecasts" 
    (
    "uid" TEXT, 
    "forecasts" TEXT, 
    "date" timestamp 
    )
    ''')
    connection.commit()
    connection.close()


def get_forecasts():
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Forecasts')
    forecasts = cursor.fetchall()
    connection.close()

    return forecasts


def get_forecasts_by_uid(uid: str):
    connection = sqlite3.connect(get_db_path(const.DB_PATH))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Forecasts WHERE uid = ?', (uid,))
    forecasts = cursor.fetchall()
    connection.close()

    return forecasts


def insert_forecast(uid: str, forecast: str):
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Forecasts (uid, forecasts, date) VALUES (?, ?, ?)', (uid, forecast, datetime.datetime.now()))
    connection.commit()
    connection.close()


def serialize(data) -> str:
    return pickle.dumps(data)


def deserialize(string: str) -> any:
    return pickle.loads(string)
