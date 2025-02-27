import sqlite3
import const
from lib import utils, telegram


def optimize_db():
    connection = sqlite3.connect(utils.get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()

    try:
        cursor.execute('VACUUM')
    except Exception as e:
        print('ERROR optimize_db VACUUM', e)
        telegram.send_message(f'ERROR optimize_db VACUUM: {e}')

    try:
        cursor.execute('REINDEX')
    except Exception as e:
        print('ERROR optimize_db REINDEX', e)
        telegram.send_message(f'ERROR optimize_db REINDEX: {e}')

    try:
        cursor.execute('PRAGMA optimize')
    except Exception as e:
        print('ERROR optimize_db PRAGMA optimize', e)
        telegram.send_message(f'ERROR optimize_db PRAGMA optimize: {e}')

    connection.commit()
    connection.close()
