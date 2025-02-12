from lib.db import forecasts_db, gpt_requests_db, learning_db, news_db, news_rate_db, predictions_db


def init_db() -> None:
    forecasts_db.init_table()
    gpt_requests_db.init_table()
    learning_db.init_table()
    news_db.init_table()
    news_rate_db.init_table()
    predictions_db.init_table()
