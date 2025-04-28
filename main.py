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
    date_utils,
)
from lib.db_2 import init, db_utils, predictions_ta_1_db, predictions_ta_1_1_db, predictions_ta_1_2_db, predictions_ta_2_db, predictions_db
from lib.learn import const

init.init_db()
db_utils.optimize_db()

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_docker():
    telegram.send_message('Скрипт ticker-analysis main запущен')
    schedule.start_schedule()
else:
    print('NOT DOCKER')

    # news.news_save.save_news()

    # for i in instruments.get_instruments_white_list():
    #     print(tech_analysis.get_tech_analysis(
    #         instrument_uid=i.uid,
    #         indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
    #         date_from=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7),
    #         date_to=datetime.datetime.now(datetime.timezone.utc),
    #     ))

    # ta_2.generate_data()
    # ta_2.learn()

    # invest_calc.get_report()

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


    for i in predictions_ta_1_db.get_predictions():
        predictions_db.insert_prediction(
            instrument_uid=i.instrument_uid,
            prediction=i.prediction,
            target_date=date_utils.parse_date(i.date) + datetime.timedelta(days=30),
            model_name=const.TA_1,
            date=i.date,
        )

    for i in predictions_ta_1_1_db.get_predictions():
        predictions_db.insert_prediction(
            instrument_uid=i.instrument_uid,
            prediction=i.prediction,
            target_date=date_utils.parse_date(i.date) + datetime.timedelta(days=30),
            model_name=const.TA_1_1,
            date=i.date,
        )

    for i in predictions_ta_1_2_db.get_predictions():
        predictions_db.insert_prediction(
            instrument_uid=i.instrument_uid,
            prediction=i.prediction,
            target_date=date_utils.parse_date(i.date) + datetime.timedelta(days=30),
            model_name=const.TA_1_2,
            date=i.date,
        )

    for i in predictions_ta_2_db.get_predictions():
        predictions_db.insert_prediction(
            instrument_uid=i.instrument_uid,
            prediction=i.prediction,
            target_date=date_utils.parse_date(i.date) + datetime.timedelta(days=30),
            model_name=const.TA_2,
            date=i.date,
        )

