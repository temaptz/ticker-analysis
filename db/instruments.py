import sqlite3


def init_table():
    connection = sqlite3.connect('../db.sqlite')
    cursor = connection.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS 
    "Instruments" 
    (
    "figi" TEXT, 
    "ticker" TEXT, 
    "name" TEXT, 
    PRIMARY KEY("figi") 
    )
    ''')
    connection.commit()
    connection.close()


def get_instruments():
    connection = sqlite3.connect('../db.sqlite')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Instruments')
    instruments = cursor.fetchall()
    connection.close()

    return instruments

def get_instrument(figi: str):
    connection = sqlite3.connect('../db.sqlite')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Instruments WHERE figi = ?', (figi,))
    instrument = cursor.fetchall()
    connection.close()

    return instrument


def insert_instrument(figi: str, ticker: str, name: str):
    connection = sqlite3.connect('../db.sqlite')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Instruments (figi, ticker, name) VALUES (?, ?, ?)', (figi, ticker, name))
    connection.commit()
    connection.close()
