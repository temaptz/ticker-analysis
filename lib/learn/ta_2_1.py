import numpy as np
from t_tech.invest import InstrumentResponse, Instrument, CandleInterval
import datetime
import catboost
import pandas
from sklearn.metrics import mean_squared_error
from t_tech.invest.schemas import IndicatorType

from lib import utils, instruments, forecasts, fundamentals, news, date_utils, serializer, redis_utils, tech_analysis, yandex_disk, docker, logger
from lib.learn import learn_utils, model


def get_feature_names() -> list:
    return [
        'target_date_days',
        'name',
        'currency',
        'country_of_risk',
        'forecast_price_change',
        'market_volume',
        'rsi',
        'macd',

        'revenue_ttm',
        'ebitda_ttm',
        'market_capitalization',
        'total_debt_mrq',
        'eps_ttm',
        'pe_ratio_ttm',
        'ev_to_ebitda_mrq',
        'dividend_payout_ratio_fy',

        'news_influence_score_0',
        'news_influence_score_1',
        'news_influence_score_2',
        'news_influence_score_3',
        'news_influence_score_4',

        'price_change_2_days_min',
        'price_change_2_days_max',
        'price_change_1_week_min',
        'price_change_1_week_max',
        'price_change_2_week_min',
        'price_change_2_week_max',
        'price_change_3_week_min',
        'price_change_3_week_max',
        'price_change_1_month_min',
        'price_change_1_month_max',
        'price_change_2_month_min',
        'price_change_2_month_max',
        'price_change_3_month_min',
        'price_change_3_month_max',
        'price_change_4_month_min',
        'price_change_4_month_max',
        'price_change_5_month_min',
        'price_change_5_month_max',
        'price_change_6_month_min',
        'price_change_6_month_max',
        'price_change_7_month_min',
        'price_change_7_month_max',
        'price_change_8_month_min',
        'price_change_8_month_max',
        'price_change_9_month_min',
        'price_change_9_month_max',
        'price_change_10_month_min',
        'price_change_10_month_max',
        'price_change_11_month_min',
        'price_change_11_month_max',
        'price_change_1_year_min',
        'price_change_1_year_max',
        'price_change_2_years_min',
        'price_change_2_years_max',
        'price_change_3_years_min',
        'price_change_3_years_max',

        'price_change_2_days',
        'price_change_1_week',
        'price_change_2_week',
        'price_change_3_week',
        'price_change_1_month',
        'price_change_2_month',
        'price_change_3_month',
        'price_change_4_month',
        'price_change_5_month',
        'price_change_6_month',
        'price_change_7_month',
        'price_change_8_month',
        'price_change_9_month',
        'price_change_10_month',
        'price_change_11_month',
        'price_change_1_year',
        'price_change_2_years',
        'price_change_3_years',
    ]


def to_numpy_float(num: float) -> float:
    if num or num == 0:
        return np.float32(num)
    return np.nan


MODEL_NAME = model.TA_2_1


class Ta21LearningCard:
    is_ok: bool = True  # будет меняться в случае ошибки
    instrument: InstrumentResponse.instrument = None
    date: datetime.datetime = None  # Дата создания прогноза
    target_date: datetime.datetime = None  # Дата на которую составляется прогноз
    target_date_days: int = None  # Количество дней до даты прогнозируемой цены
    price: float = None  # Цена в дату создания прогноза
    target_price_change: float = None  # Прогнозируемая цена
    forecast_price_change: float = None  # Прогноз аналитиков
    market_volume: float = None # Объем торгов
    rsi: float = None # RSI тех.индикатор
    macd: float = None # MACD тех.индикатор

    revenue_ttm: float = None  # Выручка
    ebitda_ttm: float = None  # EBITDA
    market_capitalization: float = None  # Капитализация
    total_debt_mrq: float = None  # Долг
    eps_ttm: float = None  # EPS — прибыль на акцию
    pe_ratio_ttm: float = None  # P/E — цена/прибыль
    ev_to_ebitda_mrq: float = None  # EV/EBITDA — стоимость компании / EBITDA
    dividend_payout_ratio_fy: float = None  # DPR — коэффициент выплаты дивидендов

    news_influence_score_0: float = None  # Новостной фон 0-7 дней до даты
    news_influence_score_1: float = None  # Новостной фон 8-14 дней до даты
    news_influence_score_2: float = None  # Новостной фон 15-21 дней до даты
    news_influence_score_3: float = None  # Новостной фон 22-28 дней до даты
    news_influence_score_4: float = None  # Новостной фон 29-35 дней до даты

    price_change_2_days_min: float = None # Изменение цены за 2 дня
    price_change_2_days_max: float = None # Изменение цены за 2 дня
    price_change_1_week_min: float = None # Изменение цены за 1 неделю
    price_change_1_week_max: float = None # Изменение цены за 1 неделю
    price_change_2_week_min: float = None # Изменение цены за 2 недели
    price_change_2_week_max: float = None # Изменение цены за 2 недели
    price_change_3_week_min: float = None # Изменение цены за 3 недели
    price_change_3_week_max: float = None # Изменение цены за 3 недели
    price_change_1_month_min: float = None # Изменение цены за 1 месяц
    price_change_1_month_max: float = None # Изменение цены за 1 месяц
    price_change_2_month_min: float = None # Изменение цены за 2 месяц
    price_change_2_month_max: float = None # Изменение цены за 2 месяц
    price_change_3_month_min: float = None # Изменение цены за 3 месяца
    price_change_3_month_max: float = None # Изменение цены за 3 месяца
    price_change_4_month_min: float = None # Изменение цены за 4 месяца
    price_change_4_month_max: float = None # Изменение цены за 4 месяца
    price_change_5_month_min: float = None # Изменение цены за 5 месяца
    price_change_5_month_max: float = None # Изменение цены за 5 месяца
    price_change_6_month_min: float = None # Изменение цены за 6 месяцев
    price_change_6_month_max: float = None # Изменение цены за 6 месяцев
    price_change_7_month_min: float = None # Изменение цены за 7 месяца
    price_change_7_month_max: float = None # Изменение цены за 7 месяца
    price_change_8_month_min: float = None # Изменение цены за 8 месяца
    price_change_8_month_max: float = None # Изменение цены за 8 месяца
    price_change_9_month_min: float = None # Изменение цены за 9 месяца
    price_change_9_month_max: float = None # Изменение цены за 9 месяца
    price_change_10_month_min: float = None # Изменение цены за 10 месяца
    price_change_10_month_max: float = None # Изменение цены за 10 месяца
    price_change_11_month_min: float = None # Изменение цены за 11 месяца
    price_change_11_month_max: float = None # Изменение цены за 11 месяца
    price_change_1_year_min: float = None # Изменение цены за 1 год
    price_change_1_year_max: float = None # Изменение цены за 1 год
    price_change_2_years_min: float = None # Изменение цены за 2 года
    price_change_2_years_max: float = None # Изменение цены за 2 года
    price_change_3_years_min: float = None # Изменение цены за 3 года
    price_change_3_years_max: float = None # Изменение цены за 3 года

    price_change_2_days: float = None # Изменение цены за 2 дня
    price_change_1_week: float = None # Изменение цены за 1 неделю
    price_change_2_week: float = None # Изменение цены за 2 недели
    price_change_3_week: float = None # Изменение цены за 3 недели
    price_change_1_month: float = None # Изменение цены за 1 месяц
    price_change_2_month: float = None # Изменение цены за 2 месяц
    price_change_3_month: float = None # Изменение цены за 3 месяца
    price_change_4_month: float = None # Изменение цены за 4 месяца
    price_change_5_month: float = None # Изменение цены за 5 месяца
    price_change_6_month: float = None # Изменение цены за 6 месяцев
    price_change_7_month: float = None # Изменение цены за 7 месяцев
    price_change_8_month: float = None # Изменение цены за 8 месяцев
    price_change_9_month: float = None # Изменение цены за 9 месяцев
    price_change_10_month: float = None # Изменение цены за 10 месяцев
    price_change_11_month: float = None # Изменение цены за 11 месяцев
    price_change_1_year: float = None # Изменение цены за 1 год
    price_change_2_years: float = None # Изменение цены за 2 года
    price_change_3_years: float = None # Изменение цены за 3 года

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
            self.check_x(is_fill_empty=fill_empty)
        except Exception as e:
            print('ERROR INIT Ta21LearningCard', e)
            self.is_ok = False

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def fill_card(self, is_fill_empty=False):
        self.price = instruments.get_instrument_price_by_date(uid=self.instrument.uid, date=self.date)
        self.target_price_change = self.get_target_change_relative()
        self.forecast_price_change = self.get_forecast_change(is_fill_empty=is_fill_empty)
        self.market_volume = instruments.get_instrument_volume_by_date(uid=self.instrument.uid, date=self.date)
        self.rsi = tech_analysis.get_avg_tech_analysis_by_date(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=self.date - datetime.timedelta(days=3),
            date_to=self.date + datetime.timedelta(days=3),
        )
        self.macd = tech_analysis.get_avg_tech_analysis_by_date(
            instrument_uid=self.instrument.uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_MACD,
            date_from=self.date - datetime.timedelta(days=3),
            date_to=self.date + datetime.timedelta(days=3),
        )

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

        self.news_influence_score_0 = self.get_news_influence_score(days_from=0, days_to=7)
        self.news_influence_score_1 = self.get_news_influence_score(days_from=8, days_to=14)
        self.news_influence_score_2 = self.get_news_influence_score(days_from=15, days_to=21)
        self.news_influence_score_3 = self.get_news_influence_score(days_from=22, days_to=28)
        self.news_influence_score_4 = self.get_news_influence_score(days_from=29, days_to=35)

        self.price_change_2_days_min = self.get_price_change_days_extreme(days_count=2, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_2_days_max = self.get_price_change_days_extreme(days_count=2, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_1_week_min = self.get_price_change_days_extreme(days_count=7, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_1_week_max = self.get_price_change_days_extreme(days_count=7, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_2_week_min = self.get_price_change_days_extreme(days_count=7 * 2, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_2_week_max = self.get_price_change_days_extreme(days_count=7 * 2, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_3_week_min = self.get_price_change_days_extreme(days_count=7 * 3, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_3_week_max = self.get_price_change_days_extreme(days_count=7 * 3, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_1_month_min = self.get_price_change_days_extreme(days_count=30, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_1_month_max = self.get_price_change_days_extreme(days_count=30, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_2_month_min = self.get_price_change_days_extreme(days_count=30 * 2, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_2_month_max = self.get_price_change_days_extreme(days_count=30 * 2, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_3_month_min = self.get_price_change_days_extreme(days_count=30 * 3, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_3_month_max = self.get_price_change_days_extreme(days_count=30 * 3, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_4_month_min = self.get_price_change_days_extreme(days_count=30 * 4, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_4_month_max = self.get_price_change_days_extreme(days_count=30 * 4, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_5_month_min = self.get_price_change_days_extreme(days_count=30 * 5, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_5_month_max = self.get_price_change_days_extreme(days_count=30 * 5, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_6_month_min = self.get_price_change_days_extreme(days_count=30 * 6, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_6_month_max = self.get_price_change_days_extreme(days_count=30 * 6, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_7_month_min = self.get_price_change_days_extreme(days_count=30 * 7, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_7_month_max = self.get_price_change_days_extreme(days_count=30 * 7, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_8_month_min = self.get_price_change_days_extreme(days_count=30 * 8, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_8_month_max = self.get_price_change_days_extreme(days_count=30 * 8, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_9_month_min = self.get_price_change_days_extreme(days_count=30 * 9, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_9_month_max = self.get_price_change_days_extreme(days_count=30 * 9, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_10_month_min = self.get_price_change_days_extreme(days_count=30 * 10, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_10_month_max = self.get_price_change_days_extreme(days_count=30 * 10, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_11_month_min = self.get_price_change_days_extreme(days_count=30 * 11, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_11_month_max = self.get_price_change_days_extreme(days_count=30 * 11, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_1_year_min = self.get_price_change_days_extreme(days_count=365, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_1_year_max = self.get_price_change_days_extreme(days_count=365, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_2_years_min = self.get_price_change_days_extreme(days_count=365 * 2, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_2_years_max = self.get_price_change_days_extreme(days_count=365 * 2, is_max=True, is_fill_empty=is_fill_empty)
        self.price_change_3_years_min = self.get_price_change_days_extreme(days_count=365 * 3, is_max=False, is_fill_empty=is_fill_empty)
        self.price_change_3_years_max = self.get_price_change_days_extreme(days_count=365 * 3, is_max=True, is_fill_empty=is_fill_empty)

        self.price_change_2_days = self.get_price_change_days(days_count=2)
        self.price_change_1_week = self.get_price_change_days(days_count=7)
        self.price_change_2_week = self.get_price_change_days(days_count=7 * 2)
        self.price_change_3_week = self.get_price_change_days(days_count=7 * 3)
        self.price_change_1_month = self.get_price_change_days(days_count=30)
        self.price_change_2_month = self.get_price_change_days(days_count=30 * 2)
        self.price_change_3_month = self.get_price_change_days(days_count=30 * 3)
        self.price_change_4_month = self.get_price_change_days(days_count=30 * 4)
        self.price_change_5_month = self.get_price_change_days(days_count=30 * 5)
        self.price_change_6_month = self.get_price_change_days(days_count=30 * 6)
        self.price_change_7_month = self.get_price_change_days(days_count=30 * 7)
        self.price_change_8_month = self.get_price_change_days(days_count=30 * 8)
        self.price_change_9_month = self.get_price_change_days(days_count=30 * 9)
        self.price_change_10_month = self.get_price_change_days(days_count=30 * 10)
        self.price_change_11_month = self.get_price_change_days(days_count=30 * 11)
        self.price_change_1_year = self.get_price_change_days(days_count=365)
        self.price_change_2_years = self.get_price_change_days(days_count=365 * 2)
        self.price_change_3_years = self.get_price_change_days(days_count=365 * 3)

    # Проверка карточки
    def check_x(self, is_fill_empty=False):
        if self.price is None:
            print(f'{MODEL_NAME} CARD IS NOT OK BY CURRENT PRICE', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        if len(self.get_x()) != len(get_feature_names()):
            print(f'{MODEL_NAME} CARD IS NOT OK BY X SIZE', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        if (
                not is_fill_empty
                and (
                self.news_influence_score_0 is None
                and self.news_influence_score_1 is None
                and self.news_influence_score_2 is None
                and self.news_influence_score_3 is None
                and self.news_influence_score_4 is None
        )
        ):
            print(f'{MODEL_NAME} CARD IS NOT OK BY EMPTY NEWS', self.instrument.ticker, self.date)
            self.is_ok = False
            return

        x_values = self.get_x()
        if not all(x is not None for x in x_values):
            feature_names = get_feature_names()
            empty_fields = [name for name, value in zip(feature_names, x_values) if value is None]
            print(f'{MODEL_NAME} CARD IS OK BUT EMPTY ELEMENT IN X', self.instrument.ticker, self.date)
            print(f'Empty fields: {empty_fields}')
            # self.is_ok = False
            return

    def get_price_change_days_extreme(self, days_count: int, is_max: bool, is_fill_empty=False) -> float or None:
        if current_price := self.price:
            interval = CandleInterval.CANDLE_INTERVAL_DAY
            if days_count > 30:
                interval = CandleInterval.CANDLE_INTERVAL_WEEK
            if days_count > 300:
                interval = CandleInterval.CANDLE_INTERVAL_MONTH

            if candles := instruments.get_instrument_history_price_by_uid(
                    uid=self.instrument.uid,
                    days_count=days_count,
                    interval=interval,
                    to_date=self.date,
            ):
                if len(candles) > 0:
                    extreme_price = None

                    if is_max:
                        extreme_price = max(candles, key=lambda x: x.close).close
                    else:
                        extreme_price = min(candles, key=lambda x: x.close).close

                    if extreme_price:
                        if price_change := utils.get_change_relative_by_price(
                                main_price=current_price,
                                next_price=utils.get_price_by_quotation(extreme_price),
                        ):
                            return price_change
        return 0 if is_fill_empty else None

    def get_price_change_days(self, days_count: int) -> float or None:
        if current_price := self.price:
            if price := instruments.get_instrument_price_by_date(
                    uid=self.instrument.uid,
                    date=self.date - datetime.timedelta(days=days_count),
                    delta_hours=(24 if days_count < 30 else (24 * 7))
            ):
                if price_change := utils.get_change_relative_by_price(
                        main_price=current_price,
                        next_price=price,
                ):
                    return price_change
        return None

    def get_forecast_change(self, is_fill_empty=False) -> float or None:
        try:
            if current_price := self.price:
                if price := forecasts.get_db_forecast_by_uid_date(
                        uid=self.instrument.uid,
                        date=self.date
                ):
                    if price and len(price) > 0 and price[1] and price[1].consensus and price[1].consensus.consensus:
                        if price_forecast := utils.get_price_by_quotation(
                                price=price[1].consensus.consensus
                        ):
                            if price_change := utils.get_change_relative_by_price(main_price=current_price, next_price=price_forecast):
                                return price_change
        except Exception as e:
            logger.log_error(method_name='Ta21LearningCard.get_forecast_change', error=e, is_telegram_send=False)

        if is_fill_empty:
            return 0

        return None

    def get_news_influence_score(self, days_from: int, days_to: int) -> float or None:
        start_date = self.date - datetime.timedelta(days=days_to)
        end_date = self.date - datetime.timedelta(days=days_from)

        news_list = news.news.get_news_by_instrument_uid(
            instrument_uid=self.instrument.uid,
            start_date=start_date,
            end_date=end_date,
        ) or []
        news_ids = [n.news_uid for n in news_list]

        influence_score = news.news_rate_v2.get_news_total_influence_score(
            instrument_uid=self.instrument.uid,
            news_ids=news_ids,
        )

        if influence_score or influence_score == 0:
            return influence_score

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
            self.instrument.name, # Название актива.
            self.instrument.currency, # Валюта актива.
            self.instrument.country_of_risk, # Код страны
            to_numpy_float(self.forecast_price_change),
            to_numpy_float(self.market_volume),
            to_numpy_float(self.rsi),
            to_numpy_float(self.macd),

            to_numpy_float(self.revenue_ttm),
            to_numpy_float(self.ebitda_ttm),
            to_numpy_float(self.market_capitalization),
            to_numpy_float(self.total_debt_mrq),
            to_numpy_float(self.eps_ttm),
            to_numpy_float(self.pe_ratio_ttm),
            to_numpy_float(self.ev_to_ebitda_mrq),
            to_numpy_float(self.dividend_payout_ratio_fy),

            to_numpy_float(self.news_influence_score_0),
            to_numpy_float(self.news_influence_score_1),
            to_numpy_float(self.news_influence_score_2),
            to_numpy_float(self.news_influence_score_3),
            to_numpy_float(self.news_influence_score_4),

            to_numpy_float(self.price_change_2_days_min),
            to_numpy_float(self.price_change_2_days_max),
            to_numpy_float(self.price_change_1_week_min),
            to_numpy_float(self.price_change_1_week_max),
            to_numpy_float(self.price_change_2_week_min),
            to_numpy_float(self.price_change_2_week_max),
            to_numpy_float(self.price_change_3_week_min),
            to_numpy_float(self.price_change_3_week_max),
            to_numpy_float(self.price_change_1_month_min),
            to_numpy_float(self.price_change_1_month_max),
            to_numpy_float(self.price_change_2_month_min),
            to_numpy_float(self.price_change_2_month_max),
            to_numpy_float(self.price_change_3_month_min),
            to_numpy_float(self.price_change_3_month_max),
            to_numpy_float(self.price_change_4_month_min),
            to_numpy_float(self.price_change_4_month_max),
            to_numpy_float(self.price_change_5_month_min),
            to_numpy_float(self.price_change_5_month_max),
            to_numpy_float(self.price_change_6_month_min),
            to_numpy_float(self.price_change_6_month_max),
            to_numpy_float(self.price_change_7_month_min),
            to_numpy_float(self.price_change_7_month_max),
            to_numpy_float(self.price_change_8_month_min),
            to_numpy_float(self.price_change_8_month_max),
            to_numpy_float(self.price_change_9_month_min),
            to_numpy_float(self.price_change_9_month_max),
            to_numpy_float(self.price_change_10_month_min),
            to_numpy_float(self.price_change_10_month_max),
            to_numpy_float(self.price_change_11_month_min),
            to_numpy_float(self.price_change_11_month_max),
            to_numpy_float(self.price_change_1_year_min),
            to_numpy_float(self.price_change_1_year_max),
            to_numpy_float(self.price_change_2_years_min),
            to_numpy_float(self.price_change_2_years_max),
            to_numpy_float(self.price_change_3_years_min),
            to_numpy_float(self.price_change_3_years_max),

            to_numpy_float(self.price_change_2_days),
            to_numpy_float(self.price_change_1_week),
            to_numpy_float(self.price_change_2_week),
            to_numpy_float(self.price_change_3_week),
            to_numpy_float(self.price_change_1_month),
            to_numpy_float(self.price_change_2_month),
            to_numpy_float(self.price_change_3_month),
            to_numpy_float(self.price_change_4_month),
            to_numpy_float(self.price_change_5_month),
            to_numpy_float(self.price_change_6_month),
            to_numpy_float(self.price_change_7_month),
            to_numpy_float(self.price_change_8_month),
            to_numpy_float(self.price_change_9_month),
            to_numpy_float(self.price_change_10_month),
            to_numpy_float(self.price_change_11_month),
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
    news_beginning_date2 = news.news.news_beginning_date
    date_end = date_utils.get_day_prediction_time(date=datetime.datetime.now(tz=datetime.timezone.utc))
    date_start = date_utils.get_day_prediction_time(date=(news_beginning_date2 + datetime.timedelta(days=30)))
    instruments_list = instruments.get_instruments_white_list()
    counter_total = 0
    counter_added = 0
    counter_error = 0
    counter_cached = 0
    instrument_index = 0
    records = []
    records_keys = []

    print('GENERATE DATA TA-2_1')
    print(len(instruments_list))

    for instrument in instruments_list:
        instrument_index += 1
        print('INSTRUMENT', instrument.ticker)

        for date in date_utils.get_dates_interval_list(date_from=date_start, date_to=date_end, is_skip_holidays=True):
            print('DATE', date)

            for target_date in date_utils.get_dates_interval_list(date_from=date, date_to=date_end, is_skip_holidays=True):
                record_cache_key = get_record_cache_key(
                    ticker=instrument.ticker,
                    date=date,
                    target_date=target_date,
                )

                cached_csv_record = get_record_cache(key=record_cache_key)

                if cached_csv_record and cached_csv_record != 'error':
                    if cached_csv_record.get('result', None):
                        counter_added += 1
                        counter_cached += 1
                        records_keys.append(record_cache_key)
                    else:
                        counter_error += 1
                else:
                    card = Ta21LearningCard(
                        instrument=instrument,
                        date=date,
                        target_date=target_date,
                        fill_empty=False,
                    )

                    if card.is_ok and card.get_y() and card.get_y() != 0:
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

                print(f'(TA-2_1 PREPARE: {counter_total}; ERROR: {counter_error}; CACHED: {counter_cached}; ADDED: {counter_added}; redis: {redis_utils.get_redis_size_mb()}MB/{redis_utils.get_redis_max_size_mb()}MB; CURRENT_TICKER: {instrument.ticker}({instrument_index}/{len(instruments_list)}))')

    for key in records_keys:
        if csv_record := get_record_cache(key=key):
            records.append(csv_record)


    print('TOTAL COUNT', counter_total)
    print('TOTAL RECORDS PREPARED', len(records))

    logger.log_info(message='Данные для обучения TA_2_1 собраны', output={
        'total_count': counter_total,
        'total_records_prepared': len(records),
    })

    data_frame = pandas.DataFrame(records)

    print(data_frame)

    data_frame.to_csv(get_data_frame_csv_file_path(), index=False)

    print('DATA FRAME FILE SAVED')

    file_name = f'data_frame_ta_2_1_{date_utils.get_local_time_log_str()}.csv'

    yandex_disk.upload_file(file_path=get_data_frame_csv_file_path(), file_name=file_name)

    logger.log_info(message=f'TA-2_1 DATA FRAME file uploaded. NAME: {file_name}, SIZE: {utils.get_file_size_readable(filepath=get_data_frame_csv_file_path())}')

def learn():
    df = pandas.read_csv(get_data_frame_csv_file_path())
    x = df.drop(columns=['result'])
    y = df['result']
    text_features = []
    cat_features = ['name', 'currency', 'country_of_risk']

    x_array = x.values
    y_array = y.values
    count_samples = len(x_array)

    random_indexes = np.random.permutation(count_samples)

    x_array = x_array[random_indexes]
    y_array = y_array[random_indexes]

    # Рассчитаем точку разделения (split) на 80%, 15%, 5%
    train_end = int(0.8 * count_samples)  # после train_end заканчивается обучающая часть
    val_end = int(0.95 * count_samples)  # после val_end заканчивается валидационная часть
    # (оставшиеся 5% идут на тест)

    x_train, x_val, x_test = np.split(x_array, [train_end, val_end])
    y_train, y_val, y_test = np.split(y_array, [train_end, val_end])

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
        nan_mode='Min',
    )

    fit_start_dt = datetime.datetime.now()

    model_cb.fit(
        train_pool,
        eval_set=validate_pool,
        plot=True,
    )

    model_cb.save_model(get_model_file_path())

    y_pred_test = model_cb.predict(test_pool)
    mse_test = mean_squared_error(y_test, y_pred_test)
    rmse_test = np.sqrt(mse_test)

    # Формируем компактный, но информативный лог об обучении одной записью
    fit_end_dt = datetime.datetime.now()
    fit_duration_sec = (fit_end_dt - fit_start_dt).total_seconds()

    params = {}
    try:
        params = model_cb.get_params()
    except Exception:
        params = {}

    evals_result = None
    try:
        evals_result = model_cb.get_evals_result()
    except Exception:
        evals_result = None

    best_iteration = None
    best_score = {}
    try:
        best_iteration = model_cb.get_best_iteration()
        best_score = model_cb.get_best_score()
    except Exception:
        best_iteration = None
        best_score = {}

    # Достаём истории RMSE
    learn_rmse = []
    val_rmse = []
    if isinstance(evals_result, dict):
        learn_rmse = (evals_result.get('learn') or {}).get('RMSE') or []
        # Возможные варианты ключей для валидации: 'validation' или 'validation_0'
        val_dict = evals_result.get('validation') or evals_result.get('validation_0') or {}
        val_rmse = val_dict.get('RMSE') or []

    # Шаг логирования для TRACE
    verbose_step = 100
    if isinstance(params, dict):
        try:
            v = params.get('verbose')
            if isinstance(v, int) and v > 0:
                verbose_step = v
        except Exception:
            pass

    trace_lines = []
    total_points = len(learn_rmse)
    if total_points > 0:
        # Логируем каждые verbose_step итераций и финальную строку
        start_index = verbose_step - 1 if verbose_step > 0 else 0
        for idx in range(start_index, total_points, max(verbose_step, 1)):
            lr = learn_rmse[idx]
            vr = val_rmse[idx] if idx < len(val_rmse) else None
            trace_lines.append(f"iter={idx + 1}: learn={lr:.6f}" + (f" val={vr:.6f}" if vr is not None else ""))
        if (total_points - 1) % max(verbose_step, 1) != (max(verbose_step, 1) - 1):
            lr = learn_rmse[-1]
            vr = val_rmse[-1] if len(val_rmse) == total_points else (val_rmse[-1] if len(val_rmse) > 0 else None)
            trace_lines.append(f"iter={total_points}: learn={lr:.6f}" + (f" val={vr:.6f}" if vr is not None else "") + " (final)")

    # Лучшие метрики (если доступны)
    best_learn_rmse = None
    best_val_rmse = None
    try:
        best_learn_rmse = (best_score.get('learn') or {}).get('RMSE')
        best_val_rmse = (best_score.get('validation') or best_score.get('validation_0') or {}).get('RMSE')
    except Exception:
        best_learn_rmse = None
        best_val_rmse = None

    # Сводка параметров для читаемости
    param_line = (
        f"iterations={params.get('iterations', 10000)}, "
        f"lr={params.get('learning_rate', 0.03)}, depth={params.get('depth', 8)}, "
        f"l2_leaf_reg={params.get('l2_leaf_reg', 5)}, seed={params.get('random_seed', 42)}, "
        f"early_stopping_rounds={params.get('early_stopping_rounds', 300)}, task={params.get('task_type', 'CPU')}, "
        f"loss={params.get('loss_function', 'RMSE')}, eval={params.get('eval_metric', 'RMSE')}"
    )

    # Важность признаков (top K)
    feature_importance_line = None
    top_k = 15
    try:
        importances = model_cb.get_feature_importance(data=train_pool, type='PredictionValuesChange')
        names = get_feature_names()
        if isinstance(importances, (list, tuple)) or getattr(importances, 'shape', None):
            importances_list = list(importances)
        else:
            importances_list = []

        if len(importances_list) != len(names):
            pairs = [(f'feature_{i}', val) for i, val in enumerate(importances_list)]
        else:
            pairs = list(zip(names, importances_list))

        pairs_sorted = sorted(pairs, key=lambda x: abs(x[1]) if isinstance(x[1], (int, float)) else 0, reverse=True)
        feature_importance_line = ', '.join([f"{name}={value:.6f}" for name, value in pairs_sorted[:top_k]])
    except Exception:
        feature_importance_line = None

    log_lines = [
        f"{MODEL_NAME} LEARN",
        f"DATA: DF={len(df)} train={x_train.shape}/{y_train.shape} val={x_val.shape}/{y_val.shape} test={x_test.shape}/{y_test.shape}",
        f"PARAMS: {param_line}",
        f"FIT: started={fit_start_dt.isoformat(timespec='seconds')}, duration={fit_duration_sec:.1f}s, trees_built={getattr(model_cb, 'tree_count_', None)}",
        f"BEST: iteration={best_iteration}, learn_RMSE={best_learn_rmse}, val_RMSE={best_val_rmse}",
    ]

    if feature_importance_line:
        log_lines.append(f"FEATURE_IMPORTANCE (top {top_k}): {feature_importance_line}")

    if trace_lines:
        log_lines.append("TRACE (every ~verbose iters):")
        log_lines.extend(trace_lines)

    log_lines.append(f"TEST: RMSE={rmse_test:.6f}, MSE={mse_test:.6f}")
    log_lines.append(f"MODEL: path={get_model_file_path()}, size={utils.get_file_size_readable(filepath=get_model_file_path())}")

    logger.log_info(message='\n'.join(log_lines), is_send_telegram=True)

    learn_utils.plot_catboost_metrics(model_cb, metric_name='RMSE')


def predict_future_relative_change(
        instrument_uid: str,
        date_target: datetime.datetime,
        date_current: datetime.datetime = None,
        is_fill_empty = False,
) -> float or None:
    prediction_target_date = date_utils.get_day_prediction_time(date_target)

    card = Ta21LearningCard(
        instrument=instruments.get_instrument_by_uid(uid=instrument_uid),
        date=date_current if date_current else date_utils.get_day_prediction_time(),
        target_date=prediction_target_date,
        fill_empty=is_fill_empty,
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
        return '/app/learn_models/ta-2_1.cbm'

    return utils.get_file_abspath_recursive('ta-2_1.cbm', 'learn_models')


def get_data_frame_csv_file_path():
    if docker.is_docker():
        return '/app/ta-2_1.csv'

    return utils.get_file_abspath_recursive('ta-2_1.csv', 'data_frames')


def cache_record(card: Ta21LearningCard) -> None:
    cache_key = get_record_cache_key(
        ticker=card.instrument.ticker,
        date=card.date,
        target_date=card.target_date,
    )
    redis_utils.storage_set(key=cache_key, value=serializer.to_json(card.get_csv_record()), ttl_sec=3600 * 24 * 30)


def cache_error(
        ticker: str,
        date: datetime.datetime,
        target_date: datetime.datetime,
) -> None:
    cache_key = get_record_cache_key(
        ticker=ticker,
        date=date,
        target_date=target_date,
    )
    redis_utils.storage_set(key=cache_key, value='error', ttl_sec=3600 * 24 * 3)


def get_record_cache(key: str) -> dict or str or None:
    if record := redis_utils.storage_get(key=key):
        if record == 'error':
            return 'error'

        if parsed_record := serializer.from_json(record):
            return parsed_record
    return None


def get_record_cache_key(ticker: str, date: datetime.datetime, target_date: datetime.datetime) -> str:
    return utils.get_md5(serializer.to_json({
        'method': 'ta_2_1_record_cache_key___777',
        'ticker': ticker,
        'date': date,
        'target_date': target_date,
    }))
