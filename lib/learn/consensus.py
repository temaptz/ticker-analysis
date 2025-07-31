import numpy
from tinkoff.invest import InstrumentResponse, Instrument
import datetime
import catboost
import pandas
from sklearn.metrics import mean_squared_error
from lib import utils, instruments, forecasts, fundamentals, news, cache, date_utils, serializer, redis_utils, types_util, yandex_disk, docker, logger, predictions
from lib.news import news_rate_v1
from lib.learn import learn_utils, model


def get_feature_names() -> list:
    return ['ta_1', 'ta_1_1', 'ta_1_2', 'ta_2', 'ta_2_1']


def to_numpy_float(num: float) -> float:
    return numpy.float32(num) if num else num


MODEL_NAME = model.CONSENSUS


class ConsensusCard:
    is_ok: bool = True  # будет меняться в случае ошибки
    instrument: InstrumentResponse.instrument = None
    ta_1: float = None
    ta_1_1: float = None
    ta_1_2: float = None
    ta_2: float = None
    ta_2_1: float = None
    date: datetime.datetime = None  # Дата создания прогноза
    target_date: datetime.datetime = None  # Дата на которую составляется прогноз
    consensus: float = None  # Итоговый прогноз

    def __init__(self, instrument: Instrument, date: datetime.datetime, target_date: datetime.datetime, fill_empty=False):
        self.instrument = instrument
        self.date = date
        self.target_date = target_date

        try:
            self.fill_card()
        except Exception as e:
            print('ERROR INIT ConsensusCard', e)
            self.is_ok = False

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def fill_card(self):
        self.ta_1 = predictions.get_prediction_by_date(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            model_name=model.TA_1
        )
        self.ta_1_1 = predictions.get_prediction_by_date(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            model_name=model.TA_1_1
        )
        self.ta_1_2 = predictions.get_prediction_by_date(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            model_name=model.TA_1_2
        )
        self.ta_2 = predictions.get_prediction_by_date(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            model_name=model.TA_2
        )
        self.ta_2_1 = predictions.get_prediction_by_date(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            model_name=model.TA_2_1
        )
        if self.target_date > self.date:
            self.consensus = instruments.get_instrument_price_by_date(
                uid=self.instrument.uid,
                date=self.target_date,
                delta_hours=24 * 7
            )

    def get_x(self) -> list:
        return [
            self.ta_1,
            self.ta_1_1,
            self.ta_1_2,
            self.ta_2,
            self.ta_2_1,
        ]

    # Выходные данные для обучения
    def get_y(self) -> float:
        return self.consensus

    def get_csv_record(self) -> dict:
        result = {}
        x = self.get_x()
        y = self.get_y()
        fields_x = get_feature_names()

        for i in range(len(fields_x)):
            result[fields_x[i]] = x[i]

        result['result'] = y

        return result


def generate_data():
    date_start = datetime.datetime(year=2025, month=3, day=1, tzinfo=datetime.timezone.utc)
    date_end = datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(days=7)
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    instrument_index = 0
    records = []

    print('GENERATE DATA CONSENSUS')
    print(len(instruments_list))

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(date_from=date_start, date_to=date_end, is_skip_holidays=True):
            print('DATE', date)

            for target_date in date_utils.get_dates_interval_list(date_from=date, date_to=date_end, is_skip_holidays=True):
                card = ConsensusCard(
                    instrument=instrument,
                    date=date,
                    target_date=target_date,
                    fill_empty=False,
                )

                if card.is_ok:
                    counter_added += 1
                    records.append(card.get_csv_record())

                else:
                    counter_error += 1

                counter_total += 1

                print(f'(CONSENSUS PREPARE: {counter_total}; ERROR: {counter_error}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')

    print('TOTAL COUNT', counter_total)
    print('TOTAL RECORDS PREPARED', len(records))

    data_frame = pandas.DataFrame(records)

    print(data_frame)

    data_frame.to_csv(get_data_frame_csv_file_path(), index=False)

    print('DATA FRAME FILE SAVED')

    file_name = f'data_frame_consensus_{date_utils.get_local_time_log_str()}.csv'

    yandex_disk.upload_file(file_path=get_data_frame_csv_file_path(), file_name=file_name)

    logger.log_info(message=f'CONSENSUS DATA FRAME file uploaded. NAME: {file_name}, SIZE: {utils.get_file_size_readable(filepath=get_data_frame_csv_file_path())}')

def learn():
    df = pandas.read_csv(get_data_frame_csv_file_path())
    x = df.drop(columns=['consensus'])
    y = df['consensus']
    text_features = []
    cat_features = []

    x_array = x.values
    y_array = y.values
    count_samples = len(x_array)

    random_indexes = numpy.random.permutation(count_samples)

    x_array = x_array[random_indexes]
    y_array = y_array[random_indexes]

    # Рассчитаем точку разделения (split) на 80%, 15%, 5%
    train_end = int(0.8 * count_samples)  # после train_end заканчивается обучающая часть
    val_end = int(0.95 * count_samples)  # после val_end заканчивается валидационная часть
    # (оставшиеся 5% идут на тест)

    x_train, x_val, x_test = numpy.split(x_array, [train_end, val_end])
    y_train, y_val, y_test = numpy.split(y_array, [train_end, val_end])

    print('X_train shape:', x_train.shape)
    print('X_val shape:', x_val.shape)
    print('X_test shape:', x_test.shape)

    print('Y_train shape:', y_train.shape)
    print('Y_val shape:', y_val.shape)
    print('Y_test shape:', y_test.shape)

    train_pool = catboost.Pool(
        data=x_train,
        label=y_train,
        cat_features=cat_features,
        text_features=text_features,
        feature_names=get_feature_names(),
    )
    validate_pool = catboost.Pool(
        data=x_val,
        label=y_val,
        cat_features=cat_features,
        text_features=text_features,
        feature_names=get_feature_names(),
    )
    test_pool = catboost.Pool(
        data=x_test,
        label=y_test,
        cat_features=cat_features,
        text_features=text_features,
        feature_names=get_feature_names(),
    )

    model_cb = catboost.CatBoostRegressor(
        task_type='CPU',
        iterations=10000,
        learning_rate=0.03,
        random_seed=42,
        verbose=100,
        early_stopping_rounds=300,
        depth=8,
        l2_leaf_reg=5,
        eval_metric='RMSE',
        loss_function='RMSE',
    )

    model_cb.fit(
        train_pool,
        eval_set=validate_pool,
        plot=True,
    )

    model_cb.save_model(get_model_file_path())

    y_pred_test = model_cb.predict(test_pool)
    mse_test = mean_squared_error(y_test, y_pred_test)
    rmse_test = mean_squared_error(y_test, y_pred_test, squared=False)

    logger.log_info(message=f'{MODEL_NAME} LEARN RESULT. RMSE: {rmse_test}, MSE: {mse_test}, DATA FRAME LENGTH: {len(df)}, MODEL SIZE: {utils.get_file_size_readable(filepath=get_model_file_path())}', is_send_telegram=True)

    learn_utils.plot_catboost_metrics(model_cb, metric_name='RMSE')


@cache.ttl_cache(ttl=3600 * 24 * 30, is_skip_empty=True)
def predict_future_relative_change(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    prediction_target_date = date_target.replace(hour=12, minute=0, second=0, microsecond=0)

    card = ConsensusCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        date=datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0),
        target_date=prediction_target_date,
        fill_empty=True,
    )

    if card.is_ok:
        model = catboost.CatBoostRegressor()
        model.load_model(get_model_file_path())
        prediction = model.predict(data=card.get_x())

        if prediction:
            return utils.round_float(prediction)

    return None


def predict_future(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    if current_price := instruments.get_instrument_last_price_by_uid(uid=instrument_uid):
        if relative_change := predict_future_relative_change(instrument_uid=instrument_uid, date_target=date_target):
            if predict_price := utils.get_price_by_change_relative(current_price=current_price, relative_change=relative_change):
                return utils.round_float(predict_price, decimals=2)

    return None


def get_model_file_path():
    if docker.is_docker():
        return '/app/learn_models/ta-2_1.txt'

    return utils.get_file_abspath_recursive('ta-2_1.txt', 'learn_models')


def get_data_frame_csv_file_path():
    if docker.is_docker():
        return '/app/ta-2_1.csv'

    return utils.get_file_abspath_recursive('ta-2_1.csv', 'data_frames')


def cache_record(card: ConsensusCard) -> None:
    cache_key = get_record_cache_key(
        ticker=card.instrument.ticker,
        date=card.date,
        target_date=card.target_date,
    )
    redis_utils.storage_set(key=cache_key, value=card, ttl_sec=3600 * 24 * 30)


def cache_error(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> None:
    cache_key = get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    )
    redis_utils.storage_set(key=cache_key, value='error', ttl_sec=3600 * 24 * 3)


def get_record_cache(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> ConsensusCard or None:
    return redis_utils.storage_get(key=get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    ))


def get_record_cache_key(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> str:
    return utils.get_md5(serializer.to_json({
        'method': 'ta_2_1_get_record_cache_key_____',
        'ticker': ticker,
        'date': date,
        'target_date': target_date,
    }))
