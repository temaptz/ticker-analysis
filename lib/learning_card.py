from tinkoff.invest import (
    InstrumentResponse,
    CandleInterval,
    GetCandlesResponse,
    schemas
)
import datetime
import sys
import os
import utils
import instruments
import forecasts


class LearningCard:

    is_ok: bool = True  # будет меняться в случае ошибки
    uid: str = ''  # uid
    date: datetime.datetime  # Дата создания прогноза
    target_date: datetime.datetime  # Дата прогнозируемой цены
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

    # uid, дата когда делается прогноз, кол-во дней от этой даты до прогноза
    def __init__(self, uid: str, date: datetime.datetime, target_forecast_days: int):
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

            fundamentals = instruments.get_instrument_fundamentals_by_asset_uid(self.asset_uid)[0]
            self.revenue_ttm = fundamentals.revenue_ttm
            self.ebitda_ttm = fundamentals.ebitda_ttm
            self.market_capitalization = fundamentals.market_capitalization
            self.total_debt_mrq = fundamentals.total_debt_mrq
            self.eps_ttm = fundamentals.eps_ttm
            self.pe_ratio_ttm = fundamentals.pe_ratio_ttm
            self.ev_to_ebitda_mrq = fundamentals.ev_to_ebitda_mrq
            self.dividend_payout_ratio_fy = fundamentals.dividend_payout_ratio_fy

        except Exception:
            print('ERROR constructing LearningCard')
            self.is_ok = False

    # Вернет цены за последние 52 недели (год) в хронологическом порядке
    def get_history(self, candles: CandleInterval) -> list:
        result = []

        for i in candles[:52]:
            result.append(utils.get_price_by_candle(candle=i))

        return result

    def get_forecast(self) -> float:
        best_forecast = None

        for f in forecasts.get_db_forecasts_by_uid(uid=self.uid):
            if not best_forecast:
                best_forecast = f
                continue

            time_best = utils.parse_json_date(best_forecast and best_forecast[2])
            f_time = utils.parse_json_date(f[2])
            time_best_delta = abs(time_best - self.date)
            f_time_delta = abs(f_time - self.date)
            if f_time_delta < time_best_delta:
                best_forecast = f

        if best_forecast:
            return utils.get_price_by_quotation(price=best_forecast[1].consensus.consensus)

        return 0

    def print_card(self):
        if self.is_ok:
            print('+++')
            print('TICKER', self.ticker)
            print('DATE', self.date)
            print('DATE TARGET', self.target_date)
            print('HISTORY', self.history)
            print('PRICE', self.price)
            print('PRICE TARGET', self.target_price)
            print('PRICE CONSENSUS FORECAST', self.forecast_price)
            print('Выручка', self.revenue_ttm)
            print('EBITDA', self.ebitda_ttm)
            print('Капитализация', self.market_capitalization)
            print('Долг', self.total_debt_mrq)
            print('EPS — прибыль на акцию', self.eps_ttm)
            print('P/E — цена/прибыль', self.pe_ratio_ttm)
            print('EV/EBITDA — стоимость компании / EBITDA', self.ev_to_ebitda_mrq)
            print('DPR — коэффициент выплаты дивидендов', self.dividend_payout_ratio_fy)
            print('IS OK', self.is_ok)

        else:
            print('CARD IS BROKEN')
