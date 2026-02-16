import pandas as pd
from datetime import datetime, timedelta, timezone
from catboost import CatBoostRegressor

from lib import utils, instruments, learn, news, date_utils, serializer, redis_utils, yandex_disk, docker, logger

def generate_data():
    news_beginning_date = news.news.news_beginning_date
    yesterday = date_utils.get_day_prediction_time(date=datetime.now(timezone.utc) - timedelta(days=1))
    date_end = yesterday
    date_start = date_utils.get_day_prediction_time(date=(news_beginning_date + timedelta(days=30)))
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records = []
    records_keys = []

    print(f'GENERATE DATA {learn.model.TA_3_tech}')
    print(len(instruments_list))

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(date_from=date_start, date_to=date_end, is_skip_holidays=False, is_order_descending=not docker.is_docker()):
            print('DATE', date)

            for target_date_days in range(1, 20):
                target_date = date + timedelta(days=target_date_days)

                if target_date > date_end:
                    continue

                record_cache_key = get_record_cache_key(
                    ticker=instrument.ticker,
                    date=date,
                    target_date=target_date,
                )

                cached_csv_record = get_record_cache(key=record_cache_key)

                if cached_csv_record:
                    if cached_csv_record != 'error' and cached_csv_record.get('result', None) is not None:
                        counter_added += 1
                        counter_cached += 1
                        records_keys.append(record_cache_key)
                    else:
                        counter_error += 1
                else:
                    card = learn.ta_3_technical.Ta3TechnicalAnalysisCard(
                        instrument=instrument,
                        date=date,
                        target_date=target_date,
                        fill_empty=False,
                    )

                    if card.is_ok and card.get_y() is not None:
                        if csv_record := card.get_csv_record():
                            cache_record(card=card)
                            counter_added += 1
                            records_keys.append(record_cache_key)

                    else:
                        cache_error(
                            ticker=instrument.ticker,
                            date=date,
                            target_date=target_date,
                        )
                        counter_error += 1

                counter_total += 1

                print(f'(TA-3 PREPARE: {counter_total}; ERROR: {counter_error}; CACHED: {counter_cached}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')
    for key in records_keys:
        if csv_record := get_record_cache(key=key):
            records.append(csv_record)

    print('TOTAL COUNT', counter_total)
    print('TOTAL RECORDS PREPARED', len(records))

    logger.log_info(message='Данные для обучения TA_3 собраны', output={
        'total_count': counter_total,
        'total_records_prepared': len(records),
    })

    data_frame = pd.DataFrame(records)

    print(data_frame)

    data_frame.to_csv(get_data_frame_csv_file_path(), index=False)

    print('DATA FRAME FILE SAVED')

    file_name = f'data_frame_ta_3_{date_utils.get_local_time_log_str()}.csv'

    yandex_disk.upload_file(file_path=get_data_frame_csv_file_path(), file_name=file_name)

    logger.log_info(message=f'TA-3 DATA FRAME file uploaded. NAME: {file_name}, SIZE: {utils.get_file_size_readable(filepath=get_data_frame_csv_file_path())}')


def predict_future(
        instrument_uid: str,
        date_target: datetime,
        date_current: datetime | None = None,
        is_fill_empty=False,
) -> float | None:
    prediction_target_date = date_utils.get_day_prediction_time(date_target)
    current_date = date_current if date_current else date_utils.get_day_prediction_time()

    card = learn.ta_3_technical.Ta3TechnicalAnalysisCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        date=current_date,
        target_date=prediction_target_date,
        is_fill_empty=is_fill_empty,
    )

    if card.is_ok:
        model_cb = CatBoostRegressor()
        model_cb.load_model(get_model_file_path())
        prediction = model_cb.predict(data=card.get_x())

        if prediction is not None:
            return utils.round_float(prediction)

    return None


def get_model_file_path():
    if docker.is_docker():
        return '/app/learn_models/ta-3_technical.cbm'

    return utils.get_file_abspath_recursive('ta-3_technical.cbm', 'learn_models')


def get_data_frame_csv_file_path():
    if docker.is_docker():
        return '/app/ta-3_technical.csv'

    return utils.get_file_abspath_recursive('ta-3_technical.csv', 'data_frames')


def cache_record(card: learn.ta_3_technical.Ta3TechnicalAnalysisCard) -> None:
    cache_key = get_record_cache_key(
        ticker=card.instrument.ticker,
        date=card.date,
        target_date=card.target_date,
    )
    redis_utils.storage_set(key=cache_key, value=serializer.to_json(card.get_csv_record()), ttl_sec=3600 * 24 * 30)


def cache_error(
        ticker: str,
        date: datetime,
        target_date: datetime,
) -> None:
    cache_key = get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    )
    redis_utils.storage_set(key=cache_key, value='error', ttl_sec=3600 * 24 * 3)


def get_record_cache(key: str) -> dict | str | None:
    if record := redis_utils.storage_get(key=key):
        if record == 'error':
            return 'error'

        if parsed_record := serializer.from_json(record):
            return parsed_record
    return None


def get_record_cache_key(ticker: str, date: datetime, target_date: datetime) -> str:
    return utils.get_md5(serializer.to_json({
        'method': f'{learn.model.TA_3_tech}_record_cache_key_001',
        'ticker': ticker,
        'date': date,
        'target_date': target_date,
    }))
