from tinkoff.invest import (
    InstrumentResponse,
    CandleInterval,
    GetCandlesResponse
)
import datetime
import sys
import os


sys.path.append(os.path.abspath('./apiserver/rest/invest'))
import instruments


class LearningCard:

    uid: str = ''
    date: datetime.datetime
    ticker: str = ''
    instrument: InstrumentResponse = None
    history: GetCandlesResponse = None
    forecast = None
    fundamentals = None

    def __init__(self, uid: str, date: datetime.datetime):
        self.uid = uid
        self.date = date
        self.instrument = instruments.get_instrument_by_uid(uid=self.uid)
        self.history = instruments.get_instrument_history_price_by_uid(
            uid=self.uid,
            days_count=365,
            interval=CandleInterval.CANDLE_INTERVAL_WEEK,
            to_date=datetime.datetime.now()
        )

    def print_card(self):
        print('+++')
        print('TICKER', self.ticker)
        print('DATE', self.date)
        print('INSTRUMENT', self.instrument)
        print('HISTORY', self.history)
        print('FORECAST', self.forecast)
        print('FUNDAMENTALS', self.fundamentals)
