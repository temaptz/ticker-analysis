import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive


def init_table():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Predictions_ta_1" 
    (
    "uid" TEXT, 
    "prediction" REAL, 
    "date" timestamp 
    )
    ''')
    connection.commit()
    connection.close()


def get_predictions():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Predictions_ta_1')
    predictions = cursor.fetchall()
    connection.close()

    return predictions


def get_predictions_by_uid_date(uid: str, date_from: datetime.datetime, date_to: datetime.datetime):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('''
    SELECT * FROM Predictions_ta_1 
    WHERE uid = ?
    AND date BETWEEN ? AND ?
    ''', (
        uid,
        date_from.strftime('%Y-%m-%d 00:00:00'),
        date_to.strftime('%Y-%m-%d 23:59:59')
    ))
    predictions = cursor.fetchall()
    connection.close()

    return predictions


def insert_prediction(uid: str, prediction: float):
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Predictions_ta_1 (uid, prediction, date) VALUES (?, ?, ?)', (uid, prediction, datetime.datetime.now()))
    connection.commit()
    connection.close()
