import datetime
import os
import re
import math
import functools
import time
from tinkoff.invest import MoneyValue, Quotation, HistoricCandle, CandleInterval
import hashlib
import numpy as np
from html import unescape
from lib import date_utils, logger


def get_price_by_candle(candle: HistoricCandle) -> float or None:
    try:
        return (get_price_by_quotation(price=candle.high) + get_price_by_quotation(price=candle.low)) / 2

    except Exception as e:
        print('ERROR get_price_by_candle', e, candle)

        return None


def get_price_by_quotation(price: Quotation or MoneyValue) -> float or None:
    try:
        units = price.units or 0
        nano = price.nano or 0

        if units == 0 and nano == 0:
            return 0

        return units + nano / 1e9

    except Exception as e:
        print('ERROR get_price_by_quotation', e, price)

    return None


def get_quotation_by_price(price: float) -> Quotation or None:
    try:
        frac_part, int_part = math.modf(price)

        return Quotation(
            units=int(int_part),
            nano=int(frac_part * 1e9),
        )

    except Exception as e:
        print('ERROR get_quotation_by_price', e, price)

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
    try:
        if date:
            return date_utils.parse_date(date=date)

    except Exception as e:
        logger.log_error(method_name='parse_json_date', error=e)

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


def round_float(num: float, decimals: int = 10) -> float:
    try:
        int_len = len(str(num).split('.')[0])
        float_str = str(num)[0:int_len+decimals+5]
        float_only_digits_str = re.sub(r'[^0-9\.,]', '', float_str)

        if float_only_digits_str:
            return round(
                float(float_only_digits_str) * (1 if (num > 0) else -1),
                decimals
            )
    except Exception as e:
        logger.log_error(method_name='round_float', error=e, is_telegram_send=False)

    return num.item() if isinstance(num, np.generic) else num


def get_change_relative_by_price(main_price: float, next_price: float) -> float or None:
    try:
        return (next_price - main_price) / main_price
    except Exception as e:
        logger.log_error(method_name='get_change_relative_by_price', error=e, is_telegram_send=False)

    return None


def get_price_by_change_relative(current_price: float, relative_change: float) -> float or None:
    try:
        return current_price + (current_price * relative_change)
    except Exception as e:
        logger.log_error(method_name='get_price_by_change_relative', error=e, is_telegram_send=False)

    return None


def get_md5(data: str) -> str:
    return hashlib.md5(data.encode()).hexdigest()


@logger.error_logger
def filter_array_by_date_interval(source: list, date_field: str, interval: CandleInterval) -> list:
    filtered = []
    last_date = None
    min_interval = datetime.timedelta(seconds=date_utils.get_interval_sec_by_candle(interval=interval))

    for item in source:
        item_date = date_utils.parse_date(item[date_field])

        if last_date is None or (item_date - last_date) >= min_interval:
            filtered.append(item)
            last_date = item_date

    return filtered


def clean_news_text_for_llm(title: str, text: str, max_chars: int = 28000) -> str or None:
    if not isinstance(title, str) or not isinstance(text, str):
        return None

    result = f'{title}\n{text}'

    # Удаление base64 inline изображений
    result = re.sub(r'<img[^>]+src=["\']data:image/[^"\']+["\'][^>]*>', '', result, flags=re.IGNORECASE)

    # Удаление всех остальных HTML-тегов
    result = re.sub(r'<[^>]+>', '', result)

    # Преобразование HTML-сущностей в нормальные символы
    result = unescape(result)

    # Удаление лишних пробелов и переносов строк
    result = re.sub(r'\s+', ' ', result).strip()

    # Усечём текст до лимита символов (ориентировочно <8000 токенов)
    if len(result) > max_chars:
        result = result[:max_chars].rsplit(' ', 1)[0]  # чтобы не обрывать слово посередине

    return result


def measure_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        duration = end - start
        print(f"Время выполнения функции '{func.__name__}': {duration:.4f} секунд")
        return result
    return wrapper


def get_lots_qty(qty: int, instrument_lot: int = 1) -> int:
    return qty // instrument_lot
