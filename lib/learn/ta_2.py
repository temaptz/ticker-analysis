import numpy
from tinkoff.invest import CandleInterval, InstrumentResponse
import datetime
import catboost
import pandas
from sklearn.metrics import mean_squared_error
import const
from lib import utils, instruments, forecasts, fundamentals, news, cache, yandex, csv, date_utils, serializer, redis_utils, types, yandex_disk, docker, news_rate_v1
from lib.learn import learn_utils


class Ta2LearningCard:
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
    news_positive_percent_0: int = None  # Количество упоминаний в новостях 0-7 дней до даты
    news_negative_percent_0: int = None  # Количество упоминаний в новостях 0-7 дней до даты
    news_neutral_percent_0: int = None  # Количество упоминаний в новостях 0-7 дней до даты
    news_positive_percent_1: int = None  # Количество упоминаний в новостях 8-14 дней до даты
    news_negative_percent_1: int = None  # Количество упоминаний в новостях 8-14 дней до даты
    news_neutral_percent_1: int = None  # Количество упоминаний в новостях 8-14 дней до даты
    news_positive_percent_2: int = None  # Количество упоминаний в новостях 15-21 дней до даты
    news_negative_percent_2: int = None  # Количество упоминаний в новостях 15-21 дней до даты
    news_neutral_percent_2: int = None  # Количество упоминаний в новостях 15-21 дней до даты
    news_positive_percent_3: int = None  # Количество упоминаний в новостях 22-28 дней до даты
    news_negative_percent_3: int = None  # Количество упоминаний в новостях 22-28 дней до даты
    news_neutral_percent_3: int = None  # Количество упоминаний в новостях 22-28 дней до даты

    def __init__(self, instrument: InstrumentResponse.instrument, date: datetime.datetime, target_date: datetime.datetime, fill_empty=False):
        if date > target_date:
            self.is_ok = False
            return

        self.instrument = instrument
        self.date = date
        self.target_date = target_date

        try:
            self.fill_card(fill_empty=fill_empty)
            self.check_x()
        except Exception as e:
            print('ERROR INIT Ta2LearningCard', e)
            self.is_ok = False

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def fill_card(self, fill_empty=False):
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

        news_rated_0 = self.get_news_rated(days_from=0, days_to=7)
        news_rated_1 = self.get_news_rated(days_from=8, days_to=14)
        news_rated_2 = self.get_news_rated(days_from=15, days_to=21)
        news_rated_3 = self.get_news_rated(days_from=22, days_to=28)

        if news_rated_0:
            self.news_positive_percent_0 = news_rated_0.positive_percent
            self.news_negative_percent_0 = news_rated_0.negative_percent
            self.news_neutral_percent_0 = news_rated_0.neutral_percent

        if news_rated_1:
            self.news_positive_percent_1 = news_rated_1.positive_percent
            self.news_negative_percent_1 = news_rated_1.negative_percent
            self.news_neutral_percent_1 = news_rated_1.neutral_percent

        if news_rated_2:
            self.news_positive_percent_2 = news_rated_2.positive_percent
            self.news_negative_percent_2 = news_rated_2.negative_percent
            self.news_neutral_percent_2 = news_rated_2.neutral_percent

        if news_rated_3:
            self.news_positive_percent_3 = news_rated_3.positive_percent
            self.news_negative_percent_3 = news_rated_3.negative_percent
            self.news_neutral_percent_3 = news_rated_3.neutral_percent

    # Проверка карточки
    def check_x(self):
        if self.price is None:
            print('CARD IS NOT OK BY PRICE', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        if len(self.get_x()) != 74:
            print('CARD IS NOT OK BY X SIZE', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        if (
                self.news_positive_percent_0 is None
                or self.news_negative_percent_0 is None
                or self.news_neutral_percent_0 is None
                or self.news_positive_percent_1 is None
                or self.news_negative_percent_1 is None
                or self.news_neutral_percent_1 is None
                or self.news_positive_percent_2 is None
                or self.news_negative_percent_2 is None
                or self.news_neutral_percent_2 is None
                or self.news_positive_percent_3 is None
                or self.news_negative_percent_3 is None
                or self.news_neutral_percent_3 is None
        ):
            print('CARD IS NOT OK BY EMPTY NEWS', self.instrument.ticker, self.date)
            self.is_ok = False
            return

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

    def get_news_rated(self, days_from: int, days_to: int) -> types.NewsRate or None:
        result = None
        start_date = self.date - datetime.timedelta(days=days_to)
        end_date = self.date - datetime.timedelta(days=days_from)

        news_list = news.get_news_by_instrument_uid(
            instrument_uid=self.instrument.uid,
            start_date=start_date,
            end_date=end_date,
        )
        news_ids = [n.news_uid for n in news_list or []]
        rate = news_rate_v1.get_news_rate(news_uid_list=news_ids, instrument_uid=self.instrument.uid)

        if rate and (rate.positive_percent + rate.negative_percent + rate.neutral_percent) > 0:
            result = types.NewsRate(
                positive_percent=rate.positive_percent,
                negative_percent=rate.negative_percent,
                neutral_percent=rate.neutral_percent,
            )

        return result

    def get_target_price(self) -> float or None:
        if self.target_date < datetime.datetime.now(datetime.timezone.utc):
            return instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.target_date)

        return None

    def print_card(self):
        print('+++')
        print('TICKER', self.ticker)
        print('DATE', self.date)
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
        target_days_count = (self.target_date - self.date).days

        return [
            target_days_count,
            self.news_positive_percent_0,
            self.news_negative_percent_0,
            self.news_neutral_percent_0,
            self.news_positive_percent_1,
            self.news_negative_percent_1,
            self.news_neutral_percent_1,
            self.news_positive_percent_2,
            self.news_negative_percent_2,
            self.news_neutral_percent_2,
            self.news_positive_percent_3,
            self.news_negative_percent_3,
            self.news_neutral_percent_3,
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


def generate_data():
    news_beginning_date = datetime.datetime(year=2025, month=1, day=29)  # Самые первые новости
    news_beginning_date2 = datetime.datetime(year=2025, month=2, day=17)  # По всем тикерам
    date_end = datetime.datetime.combine(datetime.datetime.now(), datetime.time(9), tzinfo=datetime.timezone.utc)
    date_start = datetime.datetime.combine((news_beginning_date2 + datetime.timedelta(days=30)), datetime.time(9), tzinfo=datetime.timezone.utc)
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records = []

    print('GENERATE DATA TA-2')
    print(len(const.TICKER_LIST))

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

                if cached_record and cached_record != 'error':
                    counter_cached += 1
                    records.append(get_csv_record_by_learning_card(card=cached_record))
                else:
                    card = Ta2LearningCard(
                        instrument=instrument,
                        date=date,
                        target_date=target_date
                    )

                    if card.is_ok and card.get_y() and card.get_y() != 0:
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

                print(f'(TA-2 PREPARE: {counter_total}; ERROR: {counter_error}; CACHED: {counter_cached}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')

    print('TOTAL COUNT', counter_total)
    print('TOTAL RECORDS PREPARED', len(records))

    data_frame = csv.initialize_df_by_records(records=records)

    print(data_frame)

    csv.save_df_to_csv(data_frame=data_frame, filename=get_data_frame_csv_file_path())

    print('DATA FRAME FILE SAVED')

    file_name = f'data_frame_ta_2_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv'

    yandex_disk.upload_file(file_path=get_data_frame_csv_file_path(), file_name=file_name)

    print('DATA FRAME FILE UPLOADED')


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
        print('ERROR predict ta_2', e)

    return None


def predict_future(instrument_uid: str, date_target: datetime.datetime) -> float or None:
    prediction_target_date = date_target.replace(hour=12, minute=0, second=0, microsecond=0)
    cache_key = utils.get_md5(serializer.to_json({
        'method': 'ta-2_predict_future',
        'instrument_uid': instrument_uid,
        'prediction_target_date': prediction_target_date,
    }))
    cached = cache.cache_get(key=cache_key)

    if cached:
        return cached

    card = Ta2LearningCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        date=datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0),
        target_date=prediction_target_date,
        fill_empty=True,
    )

    if card.is_ok:
        prediction = predict(data=card.get_x())

        if prediction:
            cache.cache_set(key=cache_key, value=prediction, ttl=3600 * 24 * 30)

        return prediction

    return None


def get_model_file_path():
    return utils.get_file_abspath_recursive('ta-2.txt', 'learn_models')


def get_data_frame_csv_file_path():
    if docker.is_docker():
        return '/app/ta-2.csv'

    return utils.get_file_abspath_recursive('ta-2.csv', 'data_frames')


def get_csv_record_by_learning_card(card: Ta2LearningCard) -> dict:
    x = card.get_x()
    y = card.get_y()

    return {
        'target_date_days': x[0],
        'news_positive_percent_0': x[1],
        'news_negative_percent_0': x[2],
        'news_neutral_percent_0': x[3],
        'news_positive_percent_1': x[4],
        'news_negative_percent_1': x[5],
        'news_neutral_percent_1': x[6],
        'news_positive_percent_2': x[7],
        'news_negative_percent_2': x[8],
        'news_neutral_percent_2': x[9],
        'news_positive_percent_3': x[10],
        'news_negative_percent_3': x[11],
        'news_neutral_percent_3': x[12],
        'price': x[13],
        'forecast_price': x[14],
        'revenue_ttm': x[15],
        'ebitda_ttm': x[16],
        'market_capitalization': x[17],
        'total_debt_mrq': x[18],
        'eps_ttm': x[19],
        'pe_ratio_ttm': x[20],
        'ev_to_ebitda_mrq': x[21],
        'dividend_payout_ratio_fy': x[22],
        'price_week_0': x[23],
        'price_week_1': x[24],
        'price_week_2': x[25],
        'price_week_3': x[26],
        'price_week_4': x[27],
        'price_week_5': x[28],
        'price_week_6': x[29],
        'price_week_7': x[30],
        'price_week_8': x[31],
        'price_week_9': x[32],
        'price_week_10': x[33],
        'price_week_11': x[34],
        'price_week_12': x[35],
        'price_week_13': x[36],
        'price_week_14': x[37],
        'price_week_15': x[38],
        'price_week_16': x[39],
        'price_week_17': x[40],
        'price_week_18': x[41],
        'price_week_19': x[42],
        'price_week_20': x[43],
        'price_week_21': x[44],
        'price_week_22': x[45],
        'price_week_23': x[46],
        'price_week_24': x[47],
        'price_week_25': x[48],
        'price_week_26': x[49],
        'price_week_27': x[50],
        'price_week_28': x[51],
        'price_week_29': x[52],
        'price_week_30': x[53],
        'price_week_31': x[54],
        'price_week_32': x[55],
        'price_week_33': x[56],
        'price_week_34': x[57],
        'price_week_35': x[58],
        'price_week_36': x[59],
        'price_week_37': x[60],
        'price_week_38': x[61],
        'price_week_39': x[62],
        'price_week_40': x[63],
        'price_week_41': x[64],
        'price_week_42': x[65],
        'price_week_43': x[66],
        'price_week_44': x[67],
        'price_week_45': x[68],
        'price_week_46': x[69],
        'price_week_47': x[70],
        'price_week_48': x[71],
        'price_week_49': x[72],
        'price_week_50': x[73],
        'result': y,
    }


def cache_record(card: Ta2LearningCard) -> None:
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


def get_record_cache(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> Ta2LearningCard or str or None:
    return cache.cache_get(key=get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    ))


def get_record_cache_key(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> str:
    return utils.get_md5(serializer.to_json({
        'method': 'ta_2_get_record_cache_key_0',
        'ticker': ticker,
        'date': date,
        'target_date': target_date,
    }))
