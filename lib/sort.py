from lib.db import sort_instruments_db


def get_instrument_sort(instrument_uid: str) -> int or None:
    sort = sort_instruments_db.get_sort_by_uid(instrument_uid=instrument_uid)

    if sort:
        return sort[1]

    return None


def set_instrument_sort(instrument_uid: str, sort: int) -> None:
    existing_sort = sort_instruments_db.get_sort_by_uid(instrument_uid=instrument_uid)

    if existing_sort and len(existing_sort) > 0:
        sort_instruments_db.update_sort(uid=instrument_uid, sort=sort)

    else:
        sort_instruments_db.insert_sort(uid=instrument_uid, sort=sort)
