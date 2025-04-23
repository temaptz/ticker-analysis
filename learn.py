import sys
import datetime
from lib import (
    telegram,
    docker,
    schedule,
    users,
    serializer,
    news,
    fundamentals_save,
    predictions,
    predictions_save,
    utils,
    news_save,
    date_utils,
    db_2,
    yandex_disk,
    cache,
    instruments,
    invest_calc,
)
from lib.db import forecasts_db, fundamentals_db, gpt_requests_db, news_db, news_rate_db, predictions_ta_1_db, predictions_ta_1_1_db
from lib.db_2 import init, db_utils
from lib.learn import ta_1_2, ta_2

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_prod():
    ta_2.generate_data()
    # ta_2.learn()
