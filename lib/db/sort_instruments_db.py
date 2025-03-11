import datetime
import pickle
import sqlite3
import const
from lib.utils import get_file_abspath_recursive

table_name = 'Sort_instruments'


def init_table():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS "{table_name}" (
        "uid" TEXT PRIMARY KEY, 
        "sort" INTEGER, 
        "date" TIMESTAMP
    )
    ''')
    connection.commit()
    connection.close()


def get_sort():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'SELECT * FROM {table_name}')
    fundamentals = cursor.fetchall()
    connection.close()

    return fundamentals


def get_sort_by_uid(instrument_uid: str):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'''
        SELECT * FROM {table_name} 
        WHERE uid = ? 
        LIMIT 1
    ''', (instrument_uid,))
    record = cursor.fetchone()
    connection.close()

    return record


def insert_sort(uid, sort):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'''
        INSERT INTO "{table_name}" (uid, sort, date)
        VALUES (?, ?, ?)
        ''', (uid, sort, datetime.datetime.now()))
    connection.commit()
    connection.close()


def update_sort(uid, sort):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(f'''
    UPDATE "{table_name}"
    SET sort = ?, date = ?
    WHERE uid = ?
    ''', (sort, datetime.datetime.now(), uid))
    connection.commit()
    connection.close()
