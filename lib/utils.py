import datetime
import os
from tinkoff.invest.schemas import (
    Quotation,
    HistoricCandle,
)


def get_price_by_candle(candle: HistoricCandle) -> float or None:
    try:
        return (get_price_by_quotation(price=candle.high) + get_price_by_quotation(price=candle.low)) / 2

    except Exception:
        print('ERROR get_price_by_candle', candle)

        return None


def get_price_by_quotation(price: Quotation) -> float or None:
    try:
        return float(str(price.units)+'.'+str(price.nano))

    except Exception:
        print('ERROR get_price_by_candle', candle)

        return None


def get_db_path(db_path: str) -> str:
    if os.path.exists(db_path):
        return db_path

    root_directory = os.path.abspath('../')

    return root_directory+'/'+os.path.basename(db_path)


def parse_json_date(date: str or None) -> datetime.datetime or None:
    try:
        return datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')

    except Exception:
        print('ERROR parse_json_date', date)

        return None
