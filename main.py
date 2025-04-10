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
)
from lib.db import forecasts_db, fundamentals_db, gpt_requests_db, news_db, news_rate_db, predictions_ta_1_db, predictions_ta_1_1_db
from lib.db_2 import init, db_utils
from lib.learn import ta_1_2

init.init_db()
db_utils.optimize_db()

print('IS DOCKER', docker.is_docker())

if docker.is_docker():
    telegram.send_message('Скрипт ticker-analysis main запущен')
    schedule.start_schedule()
else:
    print('NOT DOCKER')

    # ta_1_2.prepare_data()
    # ta_1_2.learn()

    # db_2.migrate_sqlite.drop_tables()
    # init.init_db()
    # db_2.migrate_sqlite.copy_data_from_sqlite()
    # yandex_disk.upload_db_backup()
    # cache.clean()



    # predictions_save.save_predictions_ta_1_1()
    # ta_1_1.learn()
    # prepare_data.prepare_cards()
    # print(docker.is_prod())
    # print(docker.get_df())
    # news_db.replace_md5()
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
