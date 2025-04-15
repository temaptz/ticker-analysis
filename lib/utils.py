import datetime
import os
import re
from tinkoff.invest import MoneyValue, Quotation, HistoricCandle
import hashlib
from lib import date_utils, logger


def get_price_by_candle(candle: HistoricCandle) -> float or None:
    try:
        return (get_price_by_quotation(price=candle.high) + get_price_by_quotation(price=candle.low)) / 2

    except Exception as e:
        print('ERROR get_price_by_candle', e, candle)

        return None


def get_price_by_quotation(price: Quotation or MoneyValue) -> float or None:
    try:
        return float(str(price.units)+'.'+str(price.nano))

    except Exception as e:
        print('ERROR get_price_by_quotation', e, price)

        return None


def get_file_abspath_recursive(file_name: str, dir_name: str = '') -> str or None:
    dir_abspath = os.path.abspath(dir_name)
    db_abspath = dir_abspath+'/'+os.path.basename(file_name)

    if os.path.exists(db_abspath):
        return db_abspath

    if dir_abspath != '/':
        return get_file_abspath_recursive(file_name, os.path.dirname(dir_abspath))

    return None


def is_file_exists(file_path: str) -> bool:
    if file_path:
        return os.path.exists(file_path)

    return False


def parse_json_date(date: str or None) -> datetime.datetime or None:
    return date_utils.parse_date(date=date)


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


def round_float(num: float, decimals: int = 10) -> float:
    try:
        int_len = len(str(num).split('.')[0])
        float_str = str(num)[0:int_len+decimals+5]
        float_only_digits_str = re.sub(r'[^0-9\.,]', '', float_str)
        return round(float(float_only_digits_str), decimals)
    except Exception as e:
        logger.log_error(method_name='round_float', error=e)


def get_md5(data: str) -> str:
    return hashlib.md5(data.encode()).hexdigest()

