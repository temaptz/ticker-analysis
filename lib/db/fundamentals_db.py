import datetime
import pickle
import sqlite3
import const
from lib.utils import get_file_abspath_recursive


def init_table():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Fundamentals" 
    (
    "asset_uid" TEXT, 
    "fundamentals" TEXT, 
    "date" timestamp 
    )
    ''')
    connection.commit()
    connection.close()


def get_fundamentals():
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Fundamentals')
    fundamentals = cursor.fetchall()
    connection.close()

    return fundamentals


def get_fundamentals_by_asset_uid(asset_uid: str):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('''SELECT * FROM Fundamentals WHERE asset_uid = ? ''', (asset_uid,))
    fundamental = cursor.fetchall()
    connection.close()

    return fundamental


def get_fundamentals_by_asset_uid_date(asset_uid: str, date: datetime.datetime):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('''
        SELECT * FROM Fundamentals 
        WHERE asset_uid = ? 
        ORDER BY ABS(strftime('%s', date) - strftime('%s', ?)) 
        LIMIT 1
    ''', (asset_uid, date.strftime('%Y-%m-%d %H:%M:%S')))
    fundamental = cursor.fetchone()
    connection.close()

    return fundamental


def insert_fundamentals(asset_uid: str, fundamental: str):
    connection = sqlite3.connect(const.DB_FILENAME)
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Fundamentals (asset_uid, fundamentals, date) VALUES (?, ?, ?)', (asset_uid, fundamental, datetime.datetime.now()))
    connection.commit()
    connection.close()


def serialize(data: any) -> bytes:
    return pickle.dumps(data)


def deserialize(string: bytes) -> any:
    return pickle.loads(string)
