import datetime
import os
from tinkoff.invest.schemas import (
    Quotation,
    HistoricCandle,
)
import dateutil.parser


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
        print('ERROR get_price_by_candle', price)

        return None


def get_file_abspath_recursive(file_name: str, dir_name: str = '') -> str or None:
    dir_abspath = os.path.abspath(dir_name)
    db_abspath = dir_abspath+'/'+os.path.basename(file_name)

    if os.path.exists(db_abspath):
        return db_abspath

    if dir_abspath != '/':
        return get_file_abspath_recursive(file_name, os.path.dirname(dir_abspath))

    return None


def parse_json_date(date: str or None) -> datetime.datetime or None:
    try:
        return dateutil.parser.parse(date)

    except Exception as e:
        print('ERROR parse_json_date', date, e)

        return None


def get_file_size_readable(filepath) -> str:
    """
    Функция для получения размера файла по его абсолютному пути и преобразования его в читаемый вид.
    """
    file_size_bytes = os.path.getsize(filepath)

    # Преобразование размера из байтов в более читаемый формат
    if file_size_bytes > 1024 ** 3:
        size_str = f"{file_size_bytes / 1024 ** 3:.2f} GB"
    elif file_size_bytes > 1024 ** 2:
        size_str = f"{file_size_bytes / 1024 ** 2:.2f} MB"
    else:
        size_str = f"{file_size_bytes / 1024:.2f} KB"

    return size_str


def round_float(num: float) -> float:
    return float(str(num)[0:10])
