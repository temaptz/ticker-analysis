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

    uid: str = ''
    date: datetime.datetime
    target_date: datetime.datetime
    ticker: str = ''
    instrument: InstrumentResponse = None
    history: GetCandlesResponse = None
    forecast = None
    fundamentals = None

    def __init__(self, uid: str, date: datetime.datetime, target_forecast_days: int):
        self.uid = uid
        self.date = date
        self.target_date = (self.date + datetime.timedelta(days=target_forecast_days))
        self.instrument = instruments.get_instrument_by_uid(uid=self.uid)
        self.history = instruments.get_instrument_history_price_by_uid(
            uid=self.uid,
            days_count=365,
            interval=CandleInterval.CANDLE_INTERVAL_WEEK,
            to_date=self.date
        )

    # Вернет цены за последние 52 недели (год) в хронологическом порядке
    def get_history(self) -> list:
        result = []

        for i in self.history[:52]:
            result.append(utils.get_price_by_candle(candle=i))

        return result


    def print_card(self):
        print('+++')
        print('TICKER', self.ticker)
        print('DATE WHEN PREDICTION CREATED', self.date)
        print('DATE OF PREDICTION', self.target_date)
        print('INSTRUMENT', self.instrument)
        print('HISTORY', self.get_history())
        print('FORECAST', self.forecast)
        print('FUNDAMENTALS', self.fundamentals)
