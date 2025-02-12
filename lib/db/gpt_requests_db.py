import datetime
import sqlite3
import const
from lib.utils import get_file_abspath_recursive


def init_table():
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Gpt_requests" 
    (
    "request" TEXT,
    "response" TEXT,
    "date" timestamp
    )
    ''')
    connection.commit()
    connection.close()


def get_response(request: str) -> str or None:
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Gpt_requests WHERE request = ?', (request,))
    resp = cursor.fetchall()
    connection.close()

    if resp and len(resp) > 0 and resp[0]:
        return resp[0][1]

    return None


def insert_response(request: str, response: str):
    connection = sqlite3.connect(get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()
    cursor.execute(
        'INSERT INTO Gpt_requests (request, response, date) VALUES (?, ?, ?)',
        (request, response, datetime.datetime.now())
    )
    connection.commit()
    connection.close()
