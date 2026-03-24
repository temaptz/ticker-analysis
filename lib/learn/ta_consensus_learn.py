import pandas as pd
from datetime import datetime, timedelta, timezone
from catboost import CatBoostClassifier, CatBoostRegressor
from lib import utils, instruments, learn, date_utils, serializer, redis_utils, yandex_disk, docker, logger, users
from lib.learn import enum

def generate_data():
    date_start = date_utils.get_day_prediction_time(date=datetime(year=2025, month=2, day=1, tzinfo=timezone.utc))
    date_end = date_utils.get_day_prediction_time(date=datetime.now(timezone.utc) - timedelta(days=learn.ta_consensus_buy.TARGET_DAYS_TO))
    instruments_list = instruments.get_instruments_white_list()
    accounts = users.get_accounts()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records_keys_buy = []
    records_keys_sell = []

    print(f'GENERATE DATA {learn.model.TA_consensus_buy}')
    print(len(instruments_list))

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(
                date_from=date_start,
                date_to=date_end,
                interval_seconds=(3600 * 24 * 7),
                is_skip_holidays=False,
                is_order_descending=not docker.is_docker(),
        ):
            print('DATE', date)

            for account in accounts:
                for is_buy in [True, False]:
                    record_cache_key = get_record_cache_key(
                        ticker=instrument.ticker,
                        account_id=account.id,
                        is_buy=is_buy,
                        date=date,
                    )

                    cached_csv_record = get_record_cache(key=record_cache_key)

                    if cached_csv_record:
                        if cached_csv_record != 'error' and cached_csv_record.get('result', None) is not None:
                            counter_added += 1
                            counter_cached += 1
                            if is_buy:
                                records_keys_buy.append(record_cache_key)
                            else:
                                records_keys_sell.append(record_cache_key)
                        else:
                            counter_error += 1
                    else:
                        card = learn.ta_consensus_buy.TaConsensusBuyCard(
                            instrument=instrument,
                            account_id=account.id,
                            date=date,
                            is_fill_empty=False,
                        )

                        if card.is_ok and card.get_y() is not None:
                            if csv_record := card.get_csv_record():
                                cache_record(card=card, is_buy=is_buy)
                                counter_added += 1
                                if is_buy:
                                    records_keys_buy.append(record_cache_key)
                                else:
                                    records_keys_sell.append(record_cache_key)
                        else:
                            cache_error(
                                ticker=instrument.ticker,
                                account_id=account.id,
                                is_buy=is_buy,
                                date=date,
                            )
                            counter_error += 1

                    counter_total += 1

                    print(f'(TA-CONSENSUS-{"BUY" if is_buy else "SELL"}: {counter_total}; ERROR: {counter_error}; CACHED: {counter_cached}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')

    for is_buy in [True, False]:
        records = []
        for key in records_keys_buy if is_buy else records_keys_sell:
            if csv_record := get_record_cache(key=key):
                records.append(csv_record)

        data_frame = pd.DataFrame(records)
        df_file_path = get_data_frame_csv_file_path(is_buy=is_buy)

        print(data_frame)

        data_frame.to_csv(df_file_path, index=False)

        print('DATA FRAME FILE SAVED', df_file_path, utils.get_file_size_readable(filepath=df_file_path))

        file_name = f'data_frame_ta_consensus_{"buy" if is_buy else "sell"}_{date_utils.get_local_time_log_str()}.csv'

        yandex_disk.upload_file(file_path=df_file_path, file_name=file_name)

        logger.log_info(message=f'TA-CONSENSUS-BUY DATA FRAME file uploaded. NAME: {file_name}, SIZE: {utils.get_file_size_readable(filepath=df_file_path)}')


def predict_future(
        instrument_uid: str,
        account_id: str,
        is_buy: bool,
        date_current: datetime | None = None,
        is_fill_empty=True,
) -> float | None:
    current_date = date_current if date_current else date_utils.get_day_prediction_time()

    card = learn.ta_consensus_buy.TaConsensusBuyCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        account_id=account_id,
        date=current_date,
        is_fill_empty=is_fill_empty,
    )

    if card.is_ok:
        model_cb = CatBoostRegressor()
        model_cb.load_model(get_model_file_path(is_buy=is_buy))
        prediction = model_cb.predict(data=card.get_x())

        if prediction is not None:
            return prediction

    return None


def get_model_file_path(is_buy: bool):
    file_name = f'/app/learn_models/ta-3_consensus_{"buy" if is_buy else "sell"}.cbm'
    if docker.is_docker():
        return file_name

    return utils.get_file_abspath_recursive(file_name, 'learn_models')


def get_data_frame_csv_file_path(is_buy: bool):
    file_name = f'ta-3_consensus_{"buy" if is_buy else "sell"}.csv'
    if docker.is_docker():
        return f'/app/{file_name}'

    return utils.get_file_abspath_recursive(file_name, 'data_frames')


def cache_record(card: learn.ta_consensus_buy.TaConsensusBuyCard, is_buy: bool) -> None:
    cache_key = get_record_cache_key(
        ticker=card.instrument.ticker,
        account_id=card.account_id,
        is_buy=is_buy,
        date=card.date,
    )
    redis_utils.storage_set(key=cache_key, value=serializer.to_json(card.get_csv_record()), ttl_sec=3600 * 24 * 3)


def cache_error(
        ticker: str,
        account_id: str,
        is_buy: bool,
        date: datetime,
) -> None:
    cache_key = get_record_cache_key(
        ticker=ticker,
        account_id=account_id,
        is_buy=is_buy,
        date=date,
    )
    redis_utils.storage_set(key=cache_key, value='error', ttl_sec=3600 * 24)


def get_record_cache(key: str) -> dict | str | None:
    if record := redis_utils.storage_get(key=key):
        if record == 'error':
            return 'error'

        if parsed_record := serializer.from_json(record):
            return parsed_record
    return None


def get_record_cache_key(ticker: str, account_id: str, is_buy: bool, date: datetime) -> str:
    return utils.get_md5(serializer.to_json({
        'method': f'{learn.model.TA_consensus_buy}_cache_key_',
        'ticker': ticker,
        'account_id': account_id,
        'is_buy': 'True' if is_buy else 'False',
        'date': date,
    }))
