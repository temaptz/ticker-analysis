import datetime
import sqlite3

import const


def init_table():
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Forecasts" 
    (
    "uid" TEXT, 
    "forecasts" TEXT, 
    "date" timestamp, 
    PRIMARY KEY("uid") 
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


def insert_forecast(uid: str, forecast: str):
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Forecasts (uid, forecasts, date) VALUES (?, ?, ?)', (uid, forecast, datetime.datetime.now()))
    connection.commit()
    connection.close()
