from lib.db_2 import forecasts_db, gpt_requests_db, news_db, predictions_ta_1_db, predictions_ta_1_1_db, predictions_ta_1_2_db, predictions_ta_2_db, fundamentals_db, news_classify_requests


def init_db() -> None:
    forecasts_db.init_table()
    gpt_requests_db.init_table()
    news_db.init_tables()
    news_classify_requests.init_table()
    predictions_ta_1_db.init_table()
    predictions_ta_1_1_db.init_table()
    predictions_ta_1_2_db.init_table()
    predictions_ta_2_db.init_table()
    fundamentals_db.init_table()
