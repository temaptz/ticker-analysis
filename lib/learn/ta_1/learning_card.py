import json
import numpy
from tinkoff.invest import CandleInterval, HistoricCandle
import datetime
from lib import utils, instruments, forecasts, serializer, fundamentals


class LearningCard:

    is_ok: bool = True  # будет меняться в случае ошибки
    uid: str = ''  # uid
    asset_uid: str = ''  # asset_uid
    date: datetime.datetime = None  # Дата создания прогноза
    target_date: datetime.datetime = None  # Дата прогнозируемой цены
    ticker: str = ''
    price: float = None  # Цена в дату создания прогноза
    target_price: float = None  # Прогнозируемая цена
    history: list = []  # Список цен за год с интервалом в неделю в хронологическом порядке
    forecast_price: float = None  # Прогноз аналитиков
    revenue_ttm: float = None  # Выручка
    ebitda_ttm: float = None  # EBITDA
    market_capitalization: float = None   # Капитализация
    total_debt_mrq: float = None  # Долг
    eps_ttm: float = None  # EPS — прибыль на акцию
    pe_ratio_ttm: float = None  # P/E — цена/прибыль
    ev_to_ebitda_mrq: float = None  # EV/EBITDA — стоимость компании / EBITDA
    dividend_payout_ratio_fy: float = None  # DPR — коэффициент выплаты дивидендов

    def __init__(self):
        return

    def load_by_uid(self, uid: str, fill_empty = False, date_current: datetime.datetime = None):
        try:
            self._load_by_uid(uid=uid, fill_empty=fill_empty, date_current=date_current)
        except Exception as e:
            print('ERROR TA-1 LearningCard load_by_uid', e)
            self.is_ok = False

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def _load_by_uid(self, uid: str, fill_empty=False, date_current: datetime.datetime = None):
        self.uid = uid
        self.asset_uid = instruments.get_instrument_by_uid(uid).asset_uid
        self.date = date_current or datetime.datetime.now()
        self.ticker = instruments.get_instrument_by_uid(uid=self.uid).ticker
        self.history = self.get_history(candles=instruments.get_instrument_history_price_by_uid(
            uid=self.uid,
            days_count=365,
            interval=CandleInterval.CANDLE_INTERVAL_WEEK,
            to_date=self.date
        ))
        self.price = instruments.get_instrument_last_price_by_uid(uid=self.uid)
        self.forecast_price = utils.get_price_by_quotation(forecasts.get_forecasts(instrument_uid=self.uid).consensus.consensus)

        if fundamentals_res := fundamentals.get_db_fundamentals_by_asset_uid_date(asset_uid=self.asset_uid, date=self.date)[1]:
            self.revenue_ttm = fundamentals_res.revenue_ttm
            self.ebitda_ttm = fundamentals_res.ebitda_ttm
            self.market_capitalization = fundamentals_res.market_capitalization
            self.total_debt_mrq = fundamentals_res.total_debt_mrq
            self.eps_ttm = fundamentals_res.eps_ttm
            self.pe_ratio_ttm = fundamentals_res.pe_ratio_ttm
            self.ev_to_ebitda_mrq = fundamentals_res.ev_to_ebitda_mrq
            self.dividend_payout_ratio_fy = fundamentals_res.dividend_payout_ratio_fy
        elif fill_empty:
            self.revenue_ttm = 0
            self.ebitda_ttm = 0
            self.market_capitalization = 0
            self.total_debt_mrq = 0
            self.eps_ttm = 0
            self.pe_ratio_ttm = 0
            self.ev_to_ebitda_mrq = 0
            self.dividend_payout_ratio_fy = 0

        if fill_empty and len(self.history) < 52:
            padding = [0] * (52 - len(self.history))
            self.history = padding + self.history

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def load(self, uid: str, date: datetime.datetime, target_forecast_days: int):
        try:
            self.uid = uid
            self.asset_uid = instruments.get_instrument_by_uid(uid).asset_uid
            self.date = date
            self.target_date = (self.date + datetime.timedelta(days=target_forecast_days))
            self.ticker = instruments.get_instrument_by_uid(uid=self.uid).ticker
            self.history = self.get_history(candles=instruments.get_instrument_history_price_by_uid(
                uid=self.uid,
                days_count=365,
                interval=CandleInterval.CANDLE_INTERVAL_WEEK,
                to_date=self.date
            ))
            self.price = self.history[-1]
            self.target_price = utils.get_price_by_candle(instruments.get_instrument_history_price_by_uid(
                uid=self.uid,
                days_count=1,
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
                to_date=self.target_date
            )[0])
            self.forecast_price = self.get_forecast()

            f = fundamentals.get_db_fundamentals_by_asset_uid_date(asset_uid=self.asset_uid, date=self.date)[1]
            self.revenue_ttm = f.revenue_ttm
            self.ebitda_ttm = f.ebitda_ttm
            self.market_capitalization = f.market_capitalization
            self.total_debt_mrq = f.total_debt_mrq
            self.eps_ttm = f.eps_ttm
            self.pe_ratio_ttm = f.pe_ratio_ttm
            self.ev_to_ebitda_mrq = f.ev_to_ebitda_mrq
            self.dividend_payout_ratio_fy = f.dividend_payout_ratio_fy

        except Exception as e:
            print('ERROR loading LearningCard', e)
            self.is_ok = False

    # Вернет цены за последние 52 недели (год) в хронологическом порядке
    def get_history(self, candles: list[HistoricCandle]) -> list:
        result = []

        for i in candles[:52]:
            result.append(utils.get_price_by_candle(candle=i))

        return result

    def get_forecast(self) -> float or None:
        f = forecasts.get_db_forecast_by_uid_date(uid=self.uid, date=self.date)

        if f:
            return utils.get_price_by_quotation(price=f[1].consensus.consensus)

        return None

    def print_card(self):
        print('+++')
        print('TICKER', self.ticker)
        print('DATE', self.date)
        print('DATE TARGET', self.target_date)
        print('HISTORY', self.history)
        print('PRICE', self.price)
        print('PRICE TARGET', self.target_price)
        print('FORECAST PRICE CONSENSUS ', self.forecast_price)
        print('Выручка', self.revenue_ttm)
        print('EBITDA', self.ebitda_ttm)
        print('Капитализация', self.market_capitalization)
        print('Долг', self.total_debt_mrq)
        print('EPS — прибыль на акцию', self.eps_ttm)
        print('P/E — цена/прибыль', self.pe_ratio_ttm)
        print('EV/EBITDA — стоимость компании / EBITDA', self.ev_to_ebitda_mrq)
        print('DPR — коэффициент выплаты дивидендов', self.dividend_payout_ratio_fy)
        print('IS OK', self.is_ok)

    def get_json_db(self) -> str:
        return json.dumps(serializer.get_dict_by_object_recursive(self))

    def restore_from_json_db(self, json_data: str):
        try:
            data = json.loads(json_data)
            self.is_ok = data['is_ok']
            self.uid = data['uid']
            self.asset_uid = data['asset_uid']
            self.date = data['date']
            self.target_date = data['target_date']
            self.ticker = data['ticker']
            self.price = data['price']
            self.target_price = data['target_price']
            self.history = data['history']
            self.forecast_price = data['forecast_price']
            self.revenue_ttm = data['revenue_ttm']
            self.ebitda_ttm = data['ebitda_ttm']
            self.market_capitalization = data['market_capitalization']
            self.total_debt_mrq = data['total_debt_mrq']
            self.eps_ttm = data['eps_ttm']
            self.pe_ratio_ttm = data['pe_ratio_ttm']
            self.ev_to_ebitda_mrq = data['ev_to_ebitda_mrq']
            self.dividend_payout_ratio_fy = data['dividend_payout_ratio_fy']

        except Exception as e:
            print('ERROR restore_from_json_db LearningCard', e)
            self.is_ok = False

    # Входные данные для обучения
    def get_x(self) -> list:
        return [
            numpy.float32(self.price),
            numpy.float32(self.forecast_price),
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
