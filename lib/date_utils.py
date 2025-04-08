from dateutil import parser
import datetime
from pytz import timezone
from lib import logger


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
        date = date.replace(tzinfo=timezone('Europe/Moscow'))

    utc_datetime = date.astimezone(datetime.timezone.utc)

    return utc_datetime
