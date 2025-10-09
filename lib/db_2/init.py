from lib.db_2 import forecasts_db, gpt_requests_db, news_db, predictions_db, fundamentals_db, news_classify_requests, news_rate_2_db, instrument_tags_db, users_db


def init_db() -> None:
    print('INIT DB')
    forecasts_db.init_table()
    gpt_requests_db.init_table()
    news_db.init_tables()
    news_classify_requests.init_table()
    predictions_db.init_table()
    fundamentals_db.init_table()
    news_rate_2_db.init_table()
    instrument_tags_db.init_table()
    users_db.init_table()
