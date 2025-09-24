import holidays.countries
from dateutil import parser
import datetime
from pytz import timezone
from tinkoff.invest import CandleInterval


def parse_date(date: str or datetime.datetime) -> datetime.datetime or None:
    if isinstance(date, datetime.datetime):
        return date

    parsed_date = parser.parse(date)

    if parsed_date:
        return parsed_date

    return None


def convert_to_local(date: datetime.datetime) -> datetime.datetime:
    time_local = date.astimezone(timezone('Europe/Moscow')).replace(tzinfo=None)
    result = datetime.datetime.combine(date=time_local.date(), time=time_local.time(), tzinfo=timezone('Europe/Moscow'))

    if result:
        return result

    return date


def convert_to_utc(date: datetime.datetime) -> datetime.datetime:
    if date.tzinfo is None:
        moscow = timezone('Europe/Moscow')
        date = moscow.localize(date)

    return date.astimezone(datetime.timezone.utc)


def get_dates_interval_list(
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval_seconds=24*3600,
        is_skip_holidays=False,
        is_order_descending=False,
) -> list[datetime.datetime]:
    """
    Возвращает список дат с заданным интервалом между date_from и date_to (включительно),
    с опциональным пропуском праздничных дней (is_holiday).

    :param date_from: Начальная дата (datetime).
    :param date_to: Конечная дата (datetime).
    :param interval_seconds: Интервал между датами в секундах (по умолчанию 1 день).
    :param is_skip_holidays: Если True, пропускать праздничные дни.
    :param is_order_descending: Если True, возвращать список дат в обратном порядке.
    :return: Список дат (datetime).
    """
    result = []
    current = date_from

    while current <= date_to:
        # Пропускать праздничные, если указано
        if not is_skip_holidays or not is_holiday(current):
            result.append(current)
        current += datetime.timedelta(seconds=interval_seconds)

    return reversed(result) if is_order_descending else result


def is_holiday(date: datetime.datetime) -> bool:
    try:
        return date in holidays.country_holidays('RU')
    except Exception as e:
        print('ERROR is_holiday', e)

    return False


def get_interval_sec_by_candle(interval: CandleInterval) -> int:
    if interval == CandleInterval.CANDLE_INTERVAL_DAY:
        return 24 * 3600

    if interval == CandleInterval.CANDLE_INTERVAL_WEEK:
        return 7 * 24 * 3600

    if interval == CandleInterval.CANDLE_INTERVAL_MONTH:
        return 30 * 24 * 3600

    return 24 * 3600


def get_local_time_log_str(date=None) -> str:
    return (date or datetime.datetime.now()).strftime('%Y-%m-%d_%H-%M-%S')


def get_day_start(date: datetime.datetime) -> datetime.datetime:
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


def get_day_end(date: datetime.datetime) -> datetime.datetime:
    return date.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_day_11(date: datetime.datetime = None) -> datetime.datetime:
    return (date or datetime.datetime.now()).replace(hour=11, minute=0, second=0, microsecond=0)
