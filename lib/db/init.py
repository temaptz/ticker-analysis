import sqlite3
from lib.db import forecasts_db, gpt_requests_db, learning_db, news_db, news_rate_db, predictions_ta_1_db, fundamentals_db


def init_db() -> None:
    print('SQLITE VERSION', sqlite3.sqlite_version)

    forecasts_db.init_table()
    gpt_requests_db.init_table()
    learning_db.init_table()
    news_db.init_tables()
    news_rate_db.init_table()
    predictions_ta_1_db.init_table()
    fundamentals_db.init_table()
