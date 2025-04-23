from dateutil import parser
import datetime
from pytz import timezone
from lib import logger
from tinkoff.invest import CandleInterval


@logger.error_logger
def parse_date(date: str or datetime.datetime) -> datetime.datetime or None:
    if isinstance(date, datetime.datetime):
        return date

    parsed_date = parser.parse(date)

    if parsed_date:
        return parsed_date

    return None


@logger.error_logger
def convert_to_local(date: datetime.datetime) -> datetime.datetime:
    time_local = date.astimezone(timezone('Europe/Moscow')).replace(tzinfo=None)
    result = datetime.datetime.combine(date=time_local.date(), time=time_local.time(), tzinfo=timezone('Europe/Moscow'))

    if result:
        return result

    return date


@logger.error_logger
def convert_to_utc(date: datetime.datetime) -> datetime.datetime:
    if date.tzinfo is None:
        moscow = timezone('Europe/Moscow')
        date = moscow.localize(date)

    return date.astimezone(datetime.timezone.utc)


def get_dates_interval_list(date_from: datetime.datetime, date_to: datetime.datetime, interval_seconds=24*3600) -> list[datetime.datetime]:
    result = []

    if date_from < date_to:
        result.append(date_from)

    while len(result) > 0 and result[-1] < date_to - datetime.timedelta(seconds=interval_seconds):
        result.append(result[-1] + datetime.timedelta(seconds=interval_seconds))

    return result


def get_interval_sec_by_candle(interval: CandleInterval) -> int:
    if interval == CandleInterval.CANDLE_INTERVAL_DAY:
        return 24 * 3600

    if interval == CandleInterval.CANDLE_INTERVAL_WEEK:
        return 7 * 24 * 3600

    if interval == CandleInterval.CANDLE_INTERVAL_MONTH:
        return 30 * 24 * 3600

    return 24 * 3600


def get_local_time_log_str() -> str:
    return datetime.datetime.now(timezone('Europe/Moscow')).strftime('%Y-%m-%d_%H-%M-%S')
