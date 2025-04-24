from lib import (
    docker,
)
from lib.db import forecasts_db, fundamentals_db, gpt_requests_db, news_db, news_rate_db, predictions_ta_1_db, predictions_ta_1_1_db
from lib.learn import ta_2

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_prod():
    ta_2.generate_data()
    # ta_2.learn()
