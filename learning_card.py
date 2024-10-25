from tinkoff.invest import (
    InstrumentResponse,
    CandleInterval,
    GetCandlesResponse
)
import datetime
import sys
import os
import utils


sys.path.append(os.path.abspath('./apiserver/rest/invest'))
import instruments


class LearningCard:

    uid: str = ''  # uid
    date: datetime.datetime  # Дата создания прогноза
    target_date: datetime.datetime  # Дата прогнозируемой цены
    ticker: str = ''
    price: float = None  # Цена в дату создания прогноза
    target_price: float = None  # Прогнозируемая цена
    history: list = []  # Список цен за год с интервалом в неделю в хронологическом порядке
    forecast = None
    fundamentals = None

    def __init__(self, uid: str, date: datetime.datetime, target_forecast_days: int):
        self.uid = uid
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

    # Вернет цены за последние 52 недели (год) в хронологическом порядке
    def get_history(self, candles: CandleInterval) -> list:
        result = []

        for i in candles[:52]:
            result.append(utils.get_price_by_candle(candle=i))

        return result


    def print_card(self):
        print('+++')
        print('TICKER', self.ticker)
        print('DATE', self.date)
        print('DATE TARGET', self.target_date)
        print('HISTORY', self.history)
        print('PRICE', self.price)
        print('PRICE TARGET', self.target_price)
        print('FORECAST', self.forecast)
        print('FUNDAMENTALS', self.fundamentals)
