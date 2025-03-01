from dateutil import parser
import datetime
from pytz import timezone


def parse_date(date: str) -> datetime.datetime or None:
    try:
        parsed_date = parser.parse(date)

        if parsed_date:
            return parsed_date

    except Exception:
        return None

    return None


def convert_date_from_utc_to_local(date: datetime.datetime) -> datetime.datetime:
    try:
        time_local = date.astimezone(timezone('Europe/Moscow')).replace(tzinfo=None)

        return datetime.datetime.combine(date=time_local.date(), time=time_local.time())

    except Exception as e:
        print('ERROR convert_date_from_utc_to_local', e)

    return date


def convert_to_utc(date: datetime.datetime) -> datetime.datetime:
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone('Europe/Moscow'))

    utc_datetime = date.astimezone(datetime.timezone.utc)

    return utc_datetime
