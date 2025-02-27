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
    news_save
)
from lib.db import init, news_db, db_utils
from lib.learn import ta_2

init.init_db()
db_utils.optimize_db()


if docker.is_docker():
    telegram.send_message('Скрипт ticker-analysis main запущен')
    schedule.start_schedule()
else:
    print('NOT DOCKER')
    # ta_2.generate_data()
    # predictions_save.save_predictions()
    # news = news_db.get_news_by_date_keywords_fts(
    #     start_date=utils.parse_json_date('2025-02-14'),
    #     end_date=utils.parse_json_date('2025-02-21'),
    #     keywords=['распадская', 'распадущенская']
    # )
    #
    # print('GOT NEWS', len(news))
    # news_save.save_news()
