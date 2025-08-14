import numpy
from tinkoff.invest import InstrumentResponse, Instrument
import datetime
import catboost
import pandas
from sklearn.metrics import mean_squared_error
from lib import utils, instruments, forecasts, fundamentals, news, cache, date_utils, serializer, redis_utils, types_util, yandex_disk, docker, logger, yandex
from lib.news import news_rate_v1
from lib.learn import learn_utils, model


def get_feature_names() -> list:
    return ['target_date_days', 'name', 'currency', 'country_of_risk', 'forecast_price_change', 'revenue_ttm', 'ebitda_ttm', 'market_capitalization', 'total_debt_mrq', 'eps_ttm', 'pe_ratio_ttm', 'ev_to_ebitda_mrq', 'dividend_payout_ratio_fy', 'price_change_2_days', 'price_change_1_week', 'price_change_1_month', 'price_change_3_months', 'price_change_6_months', 'price_change_1_year', 'price_change_2_years', 'price_change_3_years']


def to_numpy_float(num: float) -> float:
    return numpy.float32(num) if num else num


class Ta12LearningCard:
    is_ok: bool = True  # будет меняться в случае ошибки
    instrument: InstrumentResponse.instrument = None
    date: datetime.datetime = None  # Дата создания прогноза
    target_date: datetime.datetime = None  # Дата на которую составляется прогноз
    target_date_days: int = None  # Количество дней до даты прогнозируемой цены
    price: float = None  # Цена в дату создания прогноза
    target_price_change: float = None  # Прогнозируемая цена
    forecast_price_change: float = None  # Прогноз аналитиков
    revenue_ttm: float = None  # Выручка
    ebitda_ttm: float = None  # EBITDA
    market_capitalization: float = None  # Капитализация
    total_debt_mrq: float = None  # Долг
    eps_ttm: float = None  # EPS — прибыль на акцию
    pe_ratio_ttm: float = None  # P/E — цена/прибыль
    ev_to_ebitda_mrq: float = None  # EV/EBITDA — стоимость компании / EBITDA
    dividend_payout_ratio_fy: float = None  # DPR — коэффициент выплаты дивидендов
    price_change_2_days: float = None # Изменение цены за 2 дня
    price_change_1_week: float = None # Изменение цены за 1 неделю
    price_change_1_month: float = None # Изменение цены за 1 месяц
    price_change_3_months: float = None # Изменение цены за 3 месяца
    price_change_6_months: float = None # Изменение цены за 6 месяцев
    price_change_1_year: float = None # Изменение цены за 1 год
    price_change_2_years: float = None # Изменение цены за 2 года
    price_change_3_years: float = None # Изменение цены за 3 года

    def __init__(self, instrument: Instrument, date: datetime.datetime, target_date: datetime.datetime, fill_empty=False):
        if date > target_date:
            self.is_ok = False
            return

        self.instrument = instrument
        self.date = date
        self.target_date = target_date

        if not self.instrument or not self.date or not self.target_date:
            self.is_ok = False
            return

        try:
            self.fill_card(is_fill_empty=fill_empty)
            self.check_x(is_fill_empty=fill_empty)
        except Exception as e:
            print('ERROR INIT Ta12LearningCard', e)
            self.is_ok = False

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def fill_card(self, is_fill_empty=False):
        self.price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)
        self.target_price_change = self.get_target_change_relative()
        self.forecast_price_change = self.get_forecast_change()
        if f := fundamentals.get_db_fundamentals_by_asset_uid_date(asset_uid=self.instrument.asset_uid, date=self.date)[1]:
            self.revenue_ttm = f.revenue_ttm
            self.ebitda_ttm = f.ebitda_ttm
            self.market_capitalization = f.market_capitalization
            self.total_debt_mrq = f.total_debt_mrq
            self.eps_ttm = f.eps_ttm
            self.pe_ratio_ttm = f.pe_ratio_ttm
            self.ev_to_ebitda_mrq = f.ev_to_ebitda_mrq
            self.dividend_payout_ratio_fy = f.dividend_payout_ratio_fy
        elif is_fill_empty:
            self.revenue_ttm = 0
            self.ebitda_ttm = 0
            self.market_capitalization = 0
            self.total_debt_mrq = 0
            self.eps_ttm = 0
            self.pe_ratio_ttm = 0
            self.ev_to_ebitda_mrq = 0
            self.dividend_payout_ratio_fy = 0

        self.price_change_2_days = self.get_price_change_days(days_count=2)
        self.price_change_1_week = self.get_price_change_days(days_count=7)
        self.price_change_1_month = self.get_price_change_days(days_count=30)
        self.price_change_3_months = self.get_price_change_days(days_count=30 * 3)
        self.price_change_6_months = self.get_price_change_days(days_count=30 * 6)
        self.price_change_1_year = self.get_price_change_days(days_count=365)
        self.price_change_2_years = self.get_price_change_days(days_count=365 * 2)
        self.price_change_3_years = self.get_price_change_days(days_count=365 * 3)


    # Проверка карточки
    def check_x(self, is_fill_empty=False):
        if self.price is None:
            print(f'{model.TA_1_2} CARD IS NOT OK BY CURRENT PRICE', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        if len(self.get_x()) != len(get_feature_names()):
            print(f'{model.TA_1_2} CARD IS NOT OK BY X SIZE', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        if not all(x is not None for x in self.get_x()):
            print(f'{model.TA_1_2} CARD IS NOT OK BY EMPTY ELEMENT IN X', self.instrument.ticker, self.date)
            print(self.get_csv_record())
            self.is_ok = False
            return

    def get_price_change_days(self, days_count: int) -> float or None:
        target_date = self.date - datetime.timedelta(days=days_count)
        if current_price := self.price:
            delta_hours = 24 * 10 if days_count > 300 else 24
            if target_price := instruments.get_instrument_price_by_date(
                    uid=self.instrument.uid,
                    date=target_date,
                    delta_hours=delta_hours,
            ):
                if price_change := utils.get_change_relative_by_price(main_price=target_price, next_price=current_price):
                    return price_change

        return None

    def get_forecast_change(self) -> float or None:
        try:
            if current_price := self.price:
                if price_forecast := utils.get_price_by_quotation(
                        price=forecasts.get_db_forecast_by_uid_date(
                            uid=self.instrument.uid,
                            date=self.date
                        )[1].consensus.consensus
                ):
                    if price_change := utils.get_change_relative_by_price(main_price=current_price, next_price=price_forecast):
                        return price_change
        except Exception as e:
            logger.log_error(method_name='Ta12LearningCard.get_forecast_change', error=e, is_telegram_send=False)

        return None

    def get_target_change_relative(self) -> float or None:
        if self.price:
            if self.target_date < datetime.datetime.now(datetime.timezone.utc):
                if target_price := instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.target_date):
                    return utils.get_change_relative_by_price(main_price=self.price, next_price=target_price)

        return None

    # Входные данные для обучения
    def get_x(self) -> list:
        target_days_count = (self.target_date - self.date).days

        return [
            target_days_count,
            self.instrument.name, # Название инструмента.
            self.instrument.currency, # Валюта инструмента.
            self.instrument.country_of_risk, # Код страны
            to_numpy_float(self.forecast_price_change),
            to_numpy_float(self.revenue_ttm),
            to_numpy_float(self.ebitda_ttm),
            to_numpy_float(self.market_capitalization),
            to_numpy_float(self.total_debt_mrq),
            to_numpy_float(self.eps_ttm),
            to_numpy_float(self.pe_ratio_ttm),
            to_numpy_float(self.ev_to_ebitda_mrq),
            to_numpy_float(self.dividend_payout_ratio_fy),
            to_numpy_float(self.price_change_2_days),
            to_numpy_float(self.price_change_1_week),
            to_numpy_float(self.price_change_1_month),
            to_numpy_float(self.price_change_3_months),
            to_numpy_float(self.price_change_6_months),
            to_numpy_float(self.price_change_1_year),
            to_numpy_float(self.price_change_2_years),
            to_numpy_float(self.price_change_3_years),
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


def generate_data():
    date_start = datetime.datetime(year=2024, month=2, day=1, hour=11, tzinfo=datetime.timezone.utc)
    date_end = datetime.datetime.combine(datetime.datetime.now(), datetime.time(11), tzinfo=datetime.timezone.utc)
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records = []

    print('GENERATE DATA TA-1_2')
    print(len(instruments_list))

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(date_from=date_start, date_to=date_end, is_skip_holidays=True):
            print('DATE', date)

            for target_date in date_utils.get_dates_interval_list(date_from=date, date_to=date_end, is_skip_holidays=True):
                cached_record = get_record_cache(
                    ticker=instrument.ticker,
                    date=date,
                    target_date=target_date,
                )

                if cached_record:
                    if cached_record != 'error':
                        if cached_csv := cached_record.get_csv_record():
                            counter_cached += 1
                            records.append(cached_csv)
                else:
                    card = Ta12LearningCard(
                        instrument=instrument,
                        date=date,
                        target_date=target_date,
                        fill_empty=False,
                    )

                    if card.is_ok and card.get_y() and card.get_y() != 0:
                        cache_record(card=card)
                        counter_added += 1
                        records.append(card.get_csv_record())

                    else:
                        cache_error(
                            ticker=instrument.ticker,
                            date=date,
                            target_date=target_date,
                        )
                        counter_error += 1

                counter_total += 1

                print(f'(TA-1_2 PREPARE: {counter_total}; ERROR: {counter_error}; CACHED: {counter_cached}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')

    print('TOTAL COUNT', counter_total)
    print('TOTAL RECORDS PREPARED', len(records))

    data_frame = pandas.DataFrame(records)

    print(data_frame)

    data_frame.to_csv(get_data_frame_csv_file_path(), index=False)

    print('DATA FRAME FILE SAVED')

    file_name = f'data_frame_ta_1_2_{date_utils.get_local_time_log_str()}.csv'

    yandex_disk.upload_file(file_path=get_data_frame_csv_file_path(), file_name=file_name)

    logger.log_info(message=f'TA-1_2 DATA FRAME file uploaded. NAME: {file_name}, SIZE: {utils.get_file_size_readable(filepath=get_data_frame_csv_file_path())}')

def learn():
    df = pandas.read_csv(get_data_frame_csv_file_path())
    x = df.drop(columns=['result'])
    y = df['result']
    text_features = ['name']
    cat_features = ['currency', 'country_of_risk']

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

    model = catboost.CatBoostRegressor(
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

    model.fit(
        train_pool,
        eval_set=validate_pool,
        plot=True,
    )

    model.save_model(get_model_file_path())

    y_pred_test = model.predict(test_pool)
    mse_test = mean_squared_error(y_test, y_pred_test)

    logger.log_info(message=f'TA-1_2 LEARN RESULT. MSE: {mse_test}, DATA FRAME LENGTH: {len(df)}, MODEL SIZE: {utils.get_file_size_readable(filepath=get_model_file_path())}', is_send_telegram=True)

    learn_utils.plot_catboost_metrics(model, metric_name='RMSE')


def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = numpy.array(y_true), numpy.array(y_pred)
    nonzero_mask = y_true != 0
    return numpy.mean(numpy.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100


@cache.ttl_cache(ttl=3600 * 24 * 30, is_skip_empty=True)
def predict_future_relative_change(
        instrument_uid: str,
        date_target: datetime.datetime,
        date_current: datetime.datetime = None,
) -> float or None:
    prediction_target_date = date_target.replace(hour=12, minute=0, second=0, microsecond=0)

    card = Ta12LearningCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        date=(date_current or datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)),
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
        return '/app/learn_models/ta-1_2.txt'

    return utils.get_file_abspath_recursive('ta-1_2.txt', 'learn_models')


def get_data_frame_csv_file_path():
    if docker.is_docker():
        return '/app/ta-1_2.csv'

    return utils.get_file_abspath_recursive('ta-1_2.csv', 'data_frames')


def cache_record(card: Ta12LearningCard) -> None:
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


def get_record_cache(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> Ta12LearningCard or None:
    return redis_utils.storage_get(key=get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    ))


def get_record_cache_key(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> str:
    return utils.get_md5(serializer.to_json({
        'method': 'ta_1_2_get_record_cache_key_0',
        'ticker': ticker,
        'date': date,
        'target_date': target_date,
    }))
