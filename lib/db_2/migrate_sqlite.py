import sqlalchemy
from lib.db import forecasts_db, fundamentals_db, gpt_requests_db, news_db, news_rate_db, predictions_ta_1_db, predictions_ta_1_1_db
from lib import db_2, date_utils, serializer


def drop_tables():
    engine = db_2.connection.get_engine()
    with engine.begin() as conn:
        conn.execute(sqlalchemy.text('''
            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                ) LOOP
                    EXECUTE 'DROP TABLE IF EXISTS public."' || r.tablename || '" CASCADE';
                END LOOP;
            END $$;
        '''))


def copy_data_from_sqlite():
    for f in forecasts_db.get_forecasts():
        print(f)
        print('UID', f[0])
        print('FORECAST', serializer.db_deserialize(f[1]))
        print('DATE', date_utils.parse_date(f[2]))
        db_2.forecasts_db.insert_forecast(instrument_uid=f[0], forecast=serializer.db_deserialize(f[1]), date=date_utils.parse_date(f[2]))

    for f in fundamentals_db.get_fundamentals():
        print(f)
        print('UID', f[0])
        print('FUNDAMENTAL', serializer.db_deserialize(f[1]))
        print('DATE', date_utils.parse_date(f[2]))
        db_2.fundamentals_db.insert_fundamentals(asset_uid=f[0], fundamental=serializer.db_deserialize(f[1]), date=date_utils.parse_date(f[2]))

    for r in gpt_requests_db.get_all():
        print(r)
        print('REQ', r[0])
        print('RES', r[1])
        print('DATE', date_utils.parse_date(r[2]))
        db_2.gpt_requests_db.insert_response(request=r[0], response=r[1], date=date_utils.parse_date(r[2]))

    for n in news_db.get_news():
        record = db_2.news_db.News(
            news_uid=n[0],
            date=date_utils.parse_date(n[1]),
            source_name=n[2],
            title=n[3],
            text=n[4]
        )

        print(n)
        print('UID', record.news_uid)
        print('DATE', record.date)
        print('SOURCE', record.source_name)
        print('TITLE', record.title)
        print('TEXT', record.text)
        db_2.news_db.insert_news(record=record)

    for r in news_rate_db.get_all():
        print(r)
        print('NEWS UID', r[0])
        print('INSTRUMENT UID', r[1])
        print('RATE', serializer.from_json(r[2]))
        print('DATE', date_utils.parse_date(r[3]))
        db_2.news_rate_db.insert_rate(news_uid=r[0], instrument_uid=r[1], rate=serializer.from_json(r[2]), date=date_utils.parse_date(r[3]))

    for p in predictions_ta_1_db.get_predictions():
        print(p)
        print('INSTRUMENT UID', p[0])
        print('PREDICTION', p[1])
        print('DATE', date_utils.parse_date(p[2]))
        db_2.predictions_ta_1_db.insert_prediction(uid=p[0], prediction=p[1], date=date_utils.parse_date(p[2]))

    for p in predictions_ta_1_1_db.get_predictions():
        print(p)
        print('INSTRUMENT UID', p[0])
        print('PREDICTION', p[1])
        print('DATE', date_utils.parse_date(p[2]))
        db_2.predictions_ta_1_1_db.insert_prediction(uid=p[0], prediction=p[1], date=date_utils.parse_date(p[2]))

