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
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Predictions')
    predictions = cursor.fetchall()
    connection.close()

    return predictions


def get_predictions_by_uid(uid: str):
    connection = sqlite3.connect(get_db_path(const.DB_PATH))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Predictions WHERE uid = ?', (uid,))
    predictions = cursor.fetchall()
    connection.close()

    return predictions


def insert_prediction(uid: str, prediction: float):
    connection = sqlite3.connect(const.DB_PATH)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Predictions (uid, prediction, date) VALUES (?, ?, ?)', (uid, prediction, datetime.datetime.now()))
    connection.commit()
    connection.close()
