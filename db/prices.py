import datetime
import sqlite3


def init_table():
    connection = sqlite3.connect('../db.sqlite')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Prices" 
    (
    "figi" TEXT, 
    "price" NUMERIC, 
    "date" timestamp, 
    PRIMARY KEY("figi") 
    )
    ''')
    connection.commit()
    connection.close()


def get_prices():
    connection = sqlite3.connect('../db.sqlite')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Prices')
    prices = cursor.fetchall()
    connection.close()

    return prices


def insert_price(figi: str, price: float):
    connection = sqlite3.connect('../db.sqlite')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Prices (figi, price, date) VALUES (?, ?, ?)', (figi, price, datetime.datetime.now()))
    connection.commit()
    connection.close()
