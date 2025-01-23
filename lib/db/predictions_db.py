import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive


def init_table():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Predictions" 
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
    cursor.execute('SELECT * FROM Predictions')
    predictions = cursor.fetchall()
    connection.close()

    return predictions


def get_predictions_by_uid(uid: str):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Predictions WHERE uid = ?', (uid,))
    predictions = cursor.fetchall()
    connection.close()

    return predictions


def insert_prediction(uid: str, prediction: float):
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Predictions (uid, prediction, date) VALUES (?, ?, ?)', (uid, prediction, datetime.datetime.now()))
    connection.commit()
    connection.close()
