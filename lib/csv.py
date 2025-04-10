import pandas as pd
import os
from lib import utils, serializer


class DataFrameManager:
    def __init__(self, filename: str):
        self.filename = filename
        self.df = self._load_dataframe()

    def _load_dataframe(self) -> pd.DataFrame:
        if os.path.exists(self.filename):
            try:
                df = pd.read_csv(self.filename)
                if not df.empty:
                    return df
            except Exception as e:
                print('ERROR loading CSV', e)
        return pd.DataFrame()

    def _get_record_id(self, record: dict) -> str:
        return utils.get_md5(serializer.to_json(record))

    def add_record(self, record: dict) -> None:
        try:
            record_id = self._get_record_id(record)
            full_record = {'id': record_id, **record}

            # Проверка на дубликаты
            if not self.df.empty and (self.df['id'] == record_id).any():
                print('Record already exists. Skipping.')
                return

            new_row = pd.DataFrame([full_record])
            self.df = pd.concat([self.df, new_row], ignore_index=True)
            self.save_to_file()
        except Exception as e:
            print('ERROR add_record', e)

    def get_dataframe(self) -> pd.DataFrame:
        return self.df

    def save_to_file(self) -> None:
        try:
            self.df.to_csv(self.filename, index=False)
        except Exception as e:
            print('ERROR save_to_file', e)

def initialize_df_by_records(records: list[dict]) -> pd.DataFrame or None:
    try:
        return pd.DataFrame([
            {'id': get_record_id(record=record), **record}
            for record in records
        ])
    except Exception as e:
        print('ERROR initialize_dataframe', e)


# def get_all_records(filename: str) -> pd.DataFrame or None:
#     try:
#         if not os.path.exists(filename):
#             return None
#
#         df = pd.read_csv(filename)
#
#         if df.empty:
#             return None
#
#         return df
#     except Exception as e:
#         print('ERROR CSV get_all_records', e)
#         return None
#
#
# def find_existing_record(filename: str, record: dict) -> pd.DataFrame or None:
#     try:
#         df = get_all_records(filename=filename)
#
#         if df is None or df.empty:
#             return None
#
#         result = df.loc[df['id'] == get_record_id(record=record)]
#
#         return result if not result.empty else None
#     except Exception as e:
#         print('ERROR CSV find_existing_record', e)
#         return None
#
#
# def add_record(filename: str, record: dict) -> None:
#     try:
#         is_empty: bool = (get_all_records(filename=filename) is None)
#         record = {'id': get_record_id(record=record), **record}
#         new_record = pd.DataFrame([record])
#         new_record.to_csv(filename, mode='a', index=False, header=is_empty)
#     except Exception as e:
#         print('ERROR CSV add_record', e)
#
#
def get_record_id(record: dict) -> str:
    return utils.get_md5(serializer.to_json(record))


def save_df_to_csv(data_frame: pd.DataFrame, filename: str) -> None:
    try:
        data_frame.to_csv(filename, index=False)
    except Exception as e:
        print('ERROR CSV add_record', e)
