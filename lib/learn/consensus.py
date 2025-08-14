import numpy
from tinkoff.invest import InstrumentResponse, Instrument, CandleInterval
import datetime
import catboost
import pandas
from sklearn.metrics import mean_squared_error
from lib import utils, instruments, forecasts, fundamentals, news, cache, date_utils, serializer, redis_utils, types_util, yandex_disk, docker, logger, predictions
from lib.learn import learn_utils, model


def get_feature_names() -> list:
    return [
        'target_date_days',
        'prediction_ta_1',
        'prediction_ta_1_1',
        'prediction_ta_1_2',
        'prediction_ta_2',
        'prediction_ta_2_1',
    ]


def to_numpy_float(num: float) -> float:
    return numpy.float32(num) if num else num


MODEL_NAME = model.CONSENSUS


class TaConsensusLearningCard:
    is_ok: bool = True  # будет меняться в случае ошибки
    instrument: InstrumentResponse.instrument = None
    date: datetime.datetime = None  # Дата создания прогноза
    target_date: datetime.datetime = None  # Дата на которую составляется прогноз
    target_date_days: int = None  # Количество дней до даты прогнозируемой цены
    target_price_change: float = None  # Прогнозируемая цена
    prediction_ta_1: float = None  # Прогноз TA-1
    prediction_ta_1_1: float = None  # Прогноз TA-1_1
    prediction_ta_1_2: float = None  # Прогноз TA-1_2
    prediction_ta_2: float = None  # Прогноз TA-2
    prediction_ta_2_1: float = None  # Прогноз TA-2_1


    def __init__(
            self,
            instrument: Instrument = None,
            date: datetime.datetime = None,
            target_date: datetime.datetime = None,
            fill_empty=False
    ):
        self.instrument = instrument
        self.date = date
        self.target_date = target_date

        if not self.instrument or not self.date or not self.target_date:
            self.is_ok = False
            return

        if date > target_date:
            self.is_ok = False
            return

        try:
            self.fill_card(is_fill_empty=fill_empty)
            self.check_x()
        except Exception as e:
            print('ERROR INIT TaConsensusLearningCard', e)
            self.is_ok = False

    def fill_card(self, is_fill_empty=False):
        current_price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)

        if current_price is None:
            self.is_ok = False
            return

        if self.target_date < datetime.datetime.now(datetime.timezone.utc):
            if target_price := instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.target_date):
                self.target_price_change = utils.get_change_relative_by_price(
                    main_price=current_price,
                    next_price=target_price,
                )

        self.prediction_ta_1 = predictions.get_prediction(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            date_current=self.date,
            model_name=model.TA_1,
        )
        self.prediction_ta_1_1 = predictions.get_prediction(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            date_current=self.date,
            model_name=model.TA_1_1,
        )
        self.prediction_ta_1_2 = predictions.get_prediction(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            date_current=self.date,
            model_name=model.TA_1_2,
        )
        self.prediction_ta_2 = predictions.get_prediction(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            date_current=self.date,
            model_name=model.TA_2,
        )
        self.prediction_ta_2_1 = predictions.get_prediction(
            instrument_uid=self.instrument.uid,
            date_target=self.target_date,
            date_current=self.date,
            model_name=model.TA_2_1,
        )

        if is_fill_empty:
            if not self.prediction_ta_1:
                self.prediction_ta_1 = 0
            if not self.prediction_ta_1_1:
                self.prediction_ta_1_1 = 0
            if not self.prediction_ta_1_2:
                self.prediction_ta_1_2 = 0
            if not self.prediction_ta_2:
                self.prediction_ta_2 = 0
            if not self.prediction_ta_2_1:
                self.prediction_ta_2_1 = 0

    # Проверка карточки
    def check_x(self):
        if not all(x is not None for x in self.get_x()):
            print(f'ERROR {MODEL_NAME} CARD IS NOT OK BY EMPTY ELEMENT IN X', self.instrument.ticker, self.date)
            print(self.get_csv_record())
            self.is_ok = False
            return

    # Входные данные для обучения
    def get_x(self) -> list:
        target_days_count = (self.target_date - self.date).days

        return [
            target_days_count,
            to_numpy_float(self.prediction_ta_1),
            to_numpy_float(self.prediction_ta_1_1),
            to_numpy_float(self.prediction_ta_1_2),
            to_numpy_float(self.prediction_ta_2),
            to_numpy_float(self.prediction_ta_2_1),
        ]

    # Выходные данные для обучения
    def get_y(self) -> float:
        return self.target_price_change

    def get_csv_record(self) -> dict:
        result = {}
        x = self.get_x()
        y = self.get_y()
        fields_x = get_feature_names()

        for i in range(len(fields_x)):
            result[fields_x[i]] = x[i]

        result['result'] = y

        return result


def learn():
    date_end = datetime.datetime.combine(datetime.datetime.now(), datetime.time(9), tzinfo=datetime.timezone.utc)
    date_start = date_end - datetime.timedelta(days=30 * 3)
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records = []

    print('GENERATE LEARN DATA CONSENSUS')

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(
            date_from=date_start,
            date_to=date_end,
            is_skip_holidays=True,
        ):
            print('DATE', date)

            for target_date in date_utils.get_dates_interval_list(date_from=date, date_to=date_end, is_skip_holidays=True):
                card = TaConsensusLearningCard(
                    instrument=instrument,
                    date=date,
                    target_date=target_date,
                    fill_empty=False,
                )

                if card.is_ok and card.get_y() and card.get_y() != 0:
                    if csv_record := card.get_csv_record():
                        counter_added += 1
                        records.append(csv_record)

                        print('ADDED RECORD', csv_record)
                else:
                    counter_error += 1

                counter_total += 1

                print(f'({MODEL_NAME} PREPARE: {counter_total}; ERROR: {counter_error}; CACHED: {counter_cached}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')

    print('TOTAL COUNT', counter_total)
    print('TOTAL RECORDS PREPARED', len(records))

    _learn(records)


def _learn(records: list[TaConsensusLearningCard]):
    df = pandas.DataFrame.from_records(records)
    x = df.drop(columns=['result'])
    y = df['result']

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
        feature_names=get_feature_names(),
    )
    validate_pool = catboost.Pool(
        data=x_val,
        label=y_val,
        feature_names=get_feature_names(),
    )
    test_pool = catboost.Pool(
        data=x_test,
        label=y_test,
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
    rmse_test = numpy.sqrt(mse_test)

    logger.log_info(message=f'{MODEL_NAME} LEARN RESULT. RMSE: {rmse_test}, MSE: {mse_test}, DATA FRAME LENGTH: {len(df)}, MODEL SIZE: {utils.get_file_size_readable(filepath=get_model_file_path())}', is_send_telegram=True)

    learn_utils.plot_catboost_metrics(model_cb, metric_name='RMSE')


@cache.ttl_cache(ttl=3600 * 24 * 30, is_skip_empty=True)
def predict_future_relative_change(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    prediction_target_date = date_target.replace(hour=12, minute=0, second=0, microsecond=0)

    card = TaConsensusLearningCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        date=datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0),
        target_date=prediction_target_date,
        fill_empty=True,
    )

    if card.is_ok:
        try:
            model = catboost.CatBoostRegressor()
            model.load_model(get_model_file_path())
            prediction = model.predict(data=card.get_x())

            if prediction:
                return utils.round_float(prediction)
        except Exception as e:
            logger.log_error(
                method_name='consensus.predict_future_relative_change',
                error=e,
                is_telegram_send=False,
            )

    return None


def predict_future(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    if current_price := instruments.get_instrument_last_price_by_uid(uid=instrument_uid):
        if relative_change := predict_future_relative_change(instrument_uid=instrument_uid, date_target=date_target):
            if predict_price := utils.get_price_by_change_relative(current_price=current_price, relative_change=relative_change):
                return utils.round_float(predict_price, decimals=2)

    return None


def get_model_file_path():
    if docker.is_docker():
        return '/app/learn_models/ta-consensus.txt'

    return utils.get_file_abspath_recursive('ta-consensus.txt', 'learn_models')
