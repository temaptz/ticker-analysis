from dateutil import parser
import datetime


def parse_date(date: str) -> datetime.datetime or None:
    try:
        parsed_date = parser.parse(date)

        if parsed_date:
            return parsed_date

    except Exception:
        return None

    return None
