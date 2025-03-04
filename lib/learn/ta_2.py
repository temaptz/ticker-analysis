import numpy
from tinkoff.invest import CandleInterval, InstrumentResponse
import datetime
import const
from lib import utils, instruments, forecasts, fundamentals, news, counter


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
    news_count_0: int = 0  # Количество упоминаний в новостях 0-7 дней до даты
    news_count_1: int = 0  # Количество упоминаний в новостях 8-14 дней до даты
    news_count_2: int = 0  # Количество упоминаний в новостях 15-21 дней до даты
    news_count_3: int = 0  # Количество упоминаний в новостях 22-28 дней до даты

    def __init__(self, instrument: InstrumentResponse.instrument, date: datetime.datetime, target_date: datetime.datetime):
        self.instrument = instrument
        self.date = date
        self.target_date = target_date

        try:
            self.fill_card()
        except Exception as e:
            print('ERROR INIT Ta2LearningCard', e)
            self.is_ok = False

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def fill_card(self):
        self.history = self.get_history()
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

        self.news_count_0 = self.get_news_count(days_from=0, days_to=7)
        self.news_count_1 = self.get_news_count(days_from=8, days_to=14)
        self.news_count_2 = self.get_news_count(days_from=15, days_to=21)
        self.news_count_3 = self.get_news_count(days_from=22, days_to=28)

    # Вернет цены за последние 52 недели (год) в хронологическом порядке
    def get_history(self) -> list:
        result = []

        candles = instruments.get_instrument_history_price_by_uid(
            uid=self.instrument.uid,
            days_count=365,
            interval=CandleInterval.CANDLE_INTERVAL_WEEK,
            to_date=self.date
        )

        for i in candles[:52]:
            result.append(utils.get_price_by_candle(candle=i))

        return result

    def get_news_count(self, days_from: int, days_to: int):
        start_date = self.date - datetime.timedelta(days=days_to)
        end_date = self.date - datetime.timedelta(days=days_from)

        n = news.get_news_by_instrument_uid(
            uid=self.instrument.uid,
            start_date=start_date,
            end_date=end_date,
        )

        return len(n or [])

    def get_target_price(self) -> float or None:
        if self.target_date < datetime.datetime.now():
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
            self.news_count_0,
            self.news_count_1,
            self.news_count_2,
            self.news_count_3,
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
    date_end = datetime.datetime.combine(datetime.datetime.now(), datetime.time(12))
    date_start = datetime.datetime.combine((news_beginning_date2 + datetime.timedelta(days=30)), datetime.time(12))
    dates = [date_start + datetime.timedelta(days=i) for i in range((date_end - date_start).days + 1)]
    counter_total = 0
    counter_success = 0

    print('GENERATE DATA TA-2')
    print(len(const.TICKER_LIST))

    for instrument in instruments.get_instruments_white_list():
        print('INSTRUMENT\n', instrument.ticker)

        for date in get_array_between_dates(date_from=date_start, date_to=date_end):

            for date_target in get_array_between_dates(date_from=date + datetime.timedelta(days=1), date_to=date_end):
                print('DATES', date, ' -> ', date_target)

                card = Ta2LearningCard(instrument=instrument, date=date, target_date=date_target)
                if card.is_ok:
                    print(counter.get_stat())
                    return
                    counter_success += 1
                counter_total += 1

    print('TOTAL CARDS', counter_total)
    print('SUCCESS', counter_success)
    print('ERRORS', counter_total - counter_success)
    print(counter.get_stat())


def get_array_between_dates(date_from: datetime.datetime, date_to: datetime.datetime) -> list[datetime.datetime]:
    result = []
    delta_hours = 24

    if date_from < date_to:
        result.append(date_from)

    while len(result) > 0 and result[-1] < date_to - datetime.timedelta(hours=delta_hours):
        result.append(result[-1] + datetime.timedelta(hours=delta_hours))

    return result
