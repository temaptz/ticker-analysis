import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive

table_name = 'Predictions_ta_1_1'


def init_table():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS 
    "{table_name}" 
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
    cursor.execute(f'SELECT * FROM {table_name}')
    predictions = cursor.fetchall()
    connection.close()

    return predictions


def get_predictions_by_uid_date(uid: str, date_from: datetime.datetime, date_to: datetime.datetime):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'''
    SELECT * FROM {table_name} 
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
    cursor.execute(f'INSERT INTO {table_name} (uid, prediction, date) VALUES (?, ?, ?)', (uid, prediction, datetime.datetime.now()))
    connection.commit()
    connection.close()
