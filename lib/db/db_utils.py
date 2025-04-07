import sqlite3
import const
from lib import utils, logger


# PRAGMA journal_mode = WAL;
# PRAGMA cache_size = -50000;
# PRAGMA temp_store = MEMORY;


def optimize_db():
    connection = sqlite3.connect(utils.get_file_abspath_recursive(const.DB_FILENAME))
    cursor = connection.cursor()

    try:
        cursor.execute('VACUUM')
    except Exception as e:
        logger.log_error(method_name='optimize_db VACUUM', error=e)

    try:
        cursor.execute('REINDEX')
    except Exception as e:
        logger.log_error(method_name='optimize_db REINDEX', error=e)

    try:
        cursor.execute('PRAGMA optimize')
    except Exception as e:
        logger.log_error(method_name='optimize_db PRAGMA optimize', error=e)

    connection.commit()
    connection.close()
