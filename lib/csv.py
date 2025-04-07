import pandas as pd
import os
from lib import utils, serializer


def get_all_records(filename: str) -> pd.DataFrame or None:
    try:
        if not os.path.exists(filename):
            return None

        df = pd.read_csv(filename)

        if df.empty:
            return None

        return df
    except Exception as e:
        print('ERROR CSV get_all_records', e)
        return None


def find_existing_record(filename: str, record: dict) -> pd.DataFrame or None:
    try:
        df = get_all_records(filename=filename)

        if df is None or df.empty:
            return None

        result = df.loc[df['id'] == get_record_id(record=record)]

        return result if not result.empty else None
    except Exception as e:
        print('ERROR CSV find_existing_record', e)
        return None


def add_record(filename: str, record: dict) -> None:
    try:
        is_empty: bool = (get_all_records(filename=filename) is None)
        record = {'id': get_record_id(record=record), **record}
        new_record = pd.DataFrame([record])
        new_record.to_csv(filename, mode='a', index=False, header=is_empty)
    except Exception as e:
        print('ERROR CSV add_record', e)


def get_record_id(record: dict) -> str:
    return utils.get_md5(serializer.to_json(record))
