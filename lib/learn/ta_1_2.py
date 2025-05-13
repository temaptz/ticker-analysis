import catboost
import pandas
import numpy
import datetime
from tinkoff.invest import CandleInterval, InstrumentResponse
from sklearn.metrics import mean_squared_error
from lib import utils, instruments, fundamentals, forecasts, csv, redis_utils, serializer, cache, date_utils, docker
from lib.learn import learn_utils


class LearningCard:
    is_ok: bool = True  # будет меняться в случае ошибки
    instrument: InstrumentResponse.instrument = None
    date: datetime.datetime = None  # Дата создания прогноза
    target_date: datetime.datetime = None  # Дата на которую составляется прогноз
    target_date_days: int = None  # Количество дней до даты прогнозируемой цены
    price: float = None  # Цена в дату создания прогноза
    target_price: float = None  # Прогнозируемая цена
    history: list = []  # Список цен за год с интервалом в неделю в хронологическом порядке
    consensus_forecast_price: float = None  # Прогноз аналитиков
    revenue_ttm: float = None  # Выручка
    ebitda_ttm: float = None  # EBITDA
    market_capitalization: float = None  # Капитализация
    total_debt_mrq: float = None  # Долг
    eps_ttm: float = None  # EPS — прибыль на акцию
    pe_ratio_ttm: float = None  # P/E — цена/прибыль
    ev_to_ebitda_mrq: float = None  # EV/EBITDA — стоимость компании / EBITDA
    dividend_payout_ratio_fy: float = None  # DPR — коэффициент выплаты дивидендов

    def __init__(
            self,
            instrument: InstrumentResponse.instrument,
            date: datetime.datetime,
            target_date: datetime.datetime,
            fill_empty=False
    ):
        if date > target_date:
            self.is_ok = False
            return

        self.instrument = instrument
        self.date = date
        self.target_date = target_date

        try:
            self.fill_card(fill_empty=fill_empty)
            self.check_self()
        except Exception as e:
            print('ERROR INIT TA-1_2 LearningCard', e)
            self.is_ok = False

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def fill_card(self, fill_empty=False):
        self.target_date_days = (self.target_date - self.date).days
        self.history = self.get_history(fill_empty=fill_empty)
        self.price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)
        self.target_price = self.get_target_price()
        self.consensus_forecast_price = utils.get_price_by_quotation(
            forecasts.get_db_forecast_by_uid_date(
                uid=self.instrument.uid,
                date=self.date
            )[1].consensus.current_price
        )

        f = fundamentals.get_db_fundamentals_by_asset_uid_date(asset_uid=self.instrument.asset_uid, date=self.date)[1]
        self.revenue_ttm = f.revenue_ttm
        self.ebitda_ttm = f.ebitda_ttm
        self.market_capitalization = f.market_capitalization
        self.total_debt_mrq = f.total_debt_mrq
        self.eps_ttm = f.eps_ttm
        self.pe_ratio_ttm = f.pe_ratio_ttm
        self.ev_to_ebitda_mrq = f.ev_to_ebitda_mrq
        self.dividend_payout_ratio_fy = f.dividend_payout_ratio_fy

    # Проверка карточки
    def check_self(self):
        if self.price is None or len(self.get_x()) != 62:
            self.is_ok = False

    # Вернет цены за последние 52 недели (год) в хронологическом порядке
    def get_history(self, fill_empty=False) -> list:
        result = []

        candles = instruments.get_instrument_history_price_by_uid(
            uid=self.instrument.uid,
            days_count=365,
            interval=CandleInterval.CANDLE_INTERVAL_WEEK,
            to_date=self.date
        )

        for i in candles[:52]:
            result.append(utils.get_price_by_candle(candle=i))

        if fill_empty and len(result) < 52:
            padding = [0] * (52 - len(result))
            result = padding + result

        return result

    def get_target_price(self) -> float or None:
        if self.target_date < datetime.datetime.now(datetime.timezone.utc):
            return instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.target_date)

        return None

    def print_card(self):
        print('+++')
        print('TICKER', self.instrument.ticker)
        print('DATE', self.date)
        print('TARGET DATE DAYS', self.target_date_days)
        print('DATE TARGET', self.target_date)
        print('HISTORY', self.history)
        print('PRICE', self.price)
        print('PRICE TARGET', self.target_price)
        print('PRICE CONSENSUS FORECAST', self.consensus_forecast_price)
        print('Выручка', self.revenue_ttm)
        print('EBITDA', self.ebitda_ttm)
        print('Капитализация', self.market_capitalization)
        print('Долг', self.total_debt_mrq)
        print('EPS — прибыль на акцию', self.eps_ttm)
        print('P/E — цена/прибыль', self.pe_ratio_ttm)
        print('EV/EBITDA — стоимость компании / EBITDA', self.ev_to_ebitda_mrq)
        print('DPR — коэффициент выплаты дивидендов', self.dividend_payout_ratio_fy)
        print('IS OK', self.is_ok)

    # Входные данные для обучения
    def get_x(self) -> list:
        return [
            self.target_date_days,
            numpy.float32(self.price),
            numpy.float32(self.consensus_forecast_price),
            numpy.float32(self.revenue_ttm),
            numpy.float32(self.ebitda_ttm),
            numpy.float32(self.market_capitalization),
            numpy.float32(self.total_debt_mrq),
            numpy.float32(self.eps_ttm),
            numpy.float32(self.pe_ratio_ttm),
            numpy.float32(self.ev_to_ebitda_mrq),
            numpy.float32(self.dividend_payout_ratio_fy)
        ] + [numpy.float32(i) for i in self.history[-51:]]

    # Выходные данные для обучения
    def get_y(self) -> float:
        return self.target_price


def get_model_file_path():
    return utils.get_file_abspath_recursive('ta-1_2.txt', 'learn_models')


def get_data_frame_csv_file_path():
    if docker.is_docker():
        return '/app/ta-1_2.csv'

    return utils.get_file_abspath_recursive('ta-1_2.csv', 'data_frames')


def learn():
    df = pandas.read_csv(get_data_frame_csv_file_path(), index_col=0)
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

    train_pool = catboost.Pool(data=x_train, label=y_train)
    validate_pool = catboost.Pool(data=x_val, label=y_val)
    test_pool = catboost.Pool(data=x_test, label=y_test)

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
    print('Test MSE:', mse_test)
    mape_test = mean_absolute_percentage_error(y_test, y_pred_test)
    print('Test MAPE:', mape_test)

    learn_utils.plot_catboost_metrics(model, metric_name='RMSE')


def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = numpy.array(y_true), numpy.array(y_pred)
    nonzero_mask = y_true != 0
    return numpy.mean(numpy.abs((y_true[nonzero_mask] - y_pred[nonzero_mask]) / y_true[nonzero_mask])) * 100


def predict(data: list) -> float or None:
    try:
        model = catboost.CatBoostRegressor()
        model.load_model(get_model_file_path())

        return model.predict(data=data)
    except Exception as e:
        print('ERROR predict ta_1_2', e)


def predict_future(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    prediction_target_date = date_target.replace(hour=12, minute=0, second=0, microsecond=0)
    cache_key = utils.get_md5(serializer.to_json({
        'method': 'ta-1_2_predict_future',
        'instrument_uid': instrument_uid,
        'prediction_target_date': prediction_target_date,
    }))
    cached = cache.cache_get(key=cache_key)

    if cached:
        return cached

    card = LearningCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        date=datetime.datetime.now(datetime.timezone.utc),
        target_date=prediction_target_date,
        fill_empty=True,
    )

    if card.is_ok:
        prediction = predict(data=card.get_x())

        if prediction:
            cache.cache_set(key=cache_key, value=prediction, ttl=3600 * 24 * 30)

        return prediction

    return None

def prepare_data():
    print('PREPARE DATA TA-1_2')

    date_start = datetime.datetime(year=2025, month=1, day=10, hour=12, tzinfo=datetime.timezone.utc)
    date_end = datetime.datetime.combine(datetime.datetime.now(), datetime.time(12), tzinfo=datetime.timezone.utc)
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records = []

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(date_from=date_start, date_to=date_end):
            print('DATE', date)

            days_until_today = len(date_utils.get_dates_interval_list(date, date_end))

            for target_days_count in range(1, days_until_today):
                target_date = (date + datetime.timedelta(days=target_days_count))
                cached_record = get_record_cache(
                    ticker=instrument.ticker,
                    date=date,
                    target_date=target_date,
                )

                if cached_record:
                    counter_cached += 1
                    if cached_record != 'error':
                        records.append(get_csv_record_by_learning_card(card=cached_record))
                else:
                    card = LearningCard(
                        instrument=instrument,
                        date=date,
                        target_date=target_date
                    )

                    if card.is_ok and card.get_y():
                        cache_record(card=card)
                        counter_added += 1
                        records.append(get_csv_record_by_learning_card(card=card))

                    else:
                        cache_error(
                            ticker=instrument.ticker,
                            date=date,
                            target_date=target_date,
                        )
                        counter_error += 1

                counter_total += 1

                print(f'(TOTAL: {counter_total}; ERROR: {counter_error}; CACHED: {counter_cached}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')

    print('TOTAL COUNT', counter_total)
    print('TOTAL RECORDS PREPARED', len(records))

    data_frame = csv.initialize_df_by_records(records=records)

    print(data_frame)

    csv.save_df_to_csv(data_frame=data_frame, filename=get_data_frame_csv_file_path())

    print('DATA FRAME FILE SAVED')



def get_csv_record_by_learning_card(card: LearningCard) -> dict:
    x = card.get_x()
    y = card.get_y()

    return {
        'target_date_days': x[0],
        'price': x[1],
        'forecast_price': x[2],
        'revenue_ttm': x[3],
        'ebitda_ttm': x[4],
        'market_capitalization': x[5],
        'total_debt_mrq': x[6],
        'eps_ttm': x[7],
        'pe_ratio_ttm': x[8],
        'ev_to_ebitda_mrq': x[9],
        'dividend_payout_ratio_fy': x[10],
        'price_week_0': x[11],
        'price_week_1': x[12],
        'price_week_2': x[13],
        'price_week_3': x[14],
        'price_week_4': x[15],
        'price_week_5': x[16],
        'price_week_6': x[17],
        'price_week_7': x[18],
        'price_week_8': x[19],
        'price_week_9': x[20],
        'price_week_10': x[21],
        'price_week_11': x[22],
        'price_week_12': x[23],
        'price_week_13': x[24],
        'price_week_14': x[25],
        'price_week_15': x[26],
        'price_week_16': x[27],
        'price_week_17': x[28],
        'price_week_18': x[29],
        'price_week_19': x[30],
        'price_week_20': x[31],
        'price_week_21': x[32],
        'price_week_22': x[33],
        'price_week_23': x[34],
        'price_week_24': x[35],
        'price_week_25': x[36],
        'price_week_26': x[37],
        'price_week_27': x[38],
        'price_week_28': x[39],
        'price_week_29': x[40],
        'price_week_30': x[41],
        'price_week_31': x[42],
        'price_week_32': x[43],
        'price_week_33': x[44],
        'price_week_34': x[45],
        'price_week_35': x[46],
        'price_week_36': x[47],
        'price_week_37': x[48],
        'price_week_38': x[49],
        'price_week_39': x[50],
        'price_week_40': x[51],
        'price_week_41': x[52],
        'price_week_42': x[53],
        'price_week_43': x[54],
        'price_week_44': x[55],
        'price_week_45': x[56],
        'price_week_46': x[57],
        'price_week_47': x[58],
        'price_week_48': x[59],
        'price_week_49': x[60],
        'price_week_50': x[61],
        'result': y,
    }


def cache_record(card: LearningCard) -> None:
    cache_key = get_record_cache_key(
        ticker=card.instrument.ticker,
        date=card.date,
        target_date=card.target_date,
    )
    cache.cache_set(key=cache_key, value=card, ttl=3600 * 24 * 365)


def cache_error(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> None:
    cache_key = get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    )
    cache.cache_set(key=cache_key, value='error', ttl=3600 * 24 * 7)


def get_record_cache(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> LearningCard or str or None:
    return cache.cache_get(key=get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    ))


def get_record_cache_key(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> str:
    return utils.get_md5(serializer.to_json({
        'method': 'ta_1_2_get_record_cache_key',
        'ticker': ticker,
        'date': date,
        'target_date': target_date,
    }))
