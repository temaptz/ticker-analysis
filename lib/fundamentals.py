import datetime
from tinkoff.invest import Client, constants, StatisticResponse
from tinkoff.invest.schemas import GetAssetFundamentalsResponse, GetAssetFundamentalsRequest
from lib import cache, utils, serializer
from lib.db_2 import fundamentals_db
from const import TINKOFF_INVEST_TOKEN


def get_fundamentals_by_asset_uid(asset_uid: str) -> list[StatisticResponse]:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_asset_fundamentals(
                request=GetAssetFundamentalsRequest(
                    assets=[asset_uid]
                )
            ).fundamentals

    except Exception as e:
        print('ERROR get_instrument_fundamentals_by_asset_uid', asset_uid, e)


def get_db_fundamentals_by_asset_uid_date(
        asset_uid: str,
        date: datetime.datetime
) -> (str, GetAssetFundamentalsResponse.fundamentals or None, str):
    if db_data := fundamentals_db.get_fundamentals_by_asset_uid_date(asset_uid, date=date):
        asset_uid = db_data.asset_uid
        date = db_data.date
        fundamentals = serializer.db_deserialize(db_data.fundamentals)

        return asset_uid, fundamentals, date
    return asset_uid, None, date


def get_db_fundamentals_by_asset_uid_date_2(asset_uid: str, date: datetime.datetime) -> StatisticResponse or None:
    db_data = fundamentals_db.get_fundamentals_by_asset_uid_date(asset_uid, date=date)

    if fundamentals := serializer.db_deserialize(db_data.fundamentals):
        return fundamentals

    return None


def get_db_fundamentals_history_by_uid(asset_uid: str):
    result = list()

    try:
        for f in fundamentals_db.get_fundamentals_by_asset_uid(asset_uid=asset_uid):
            fundamentals = serializer.db_deserialize(data=f.fundamentals)
            date = utils.parse_json_date(f.date)

            result.append({'date': date, 'fundamentals': fundamentals})

        # Фильтруем по уникальным
        result = filter_uniq(result)
        # Сортируем по дате убывания
        result = sort_by_date_desc(result)

    except Exception as e:
        print('ERROR get_db_fundamentals_history_by_uid', e)

    return result


def filter_uniq(resp):
    unique_records = []
    seen_fundamentals = set()

    for item in resp:
        # Объект StatisticResponse
        fundamentals_obj = item['fundamentals']
        # Преобразуем StatisticResponse в строку (или другой уникальный идентификатор)
        # Для protobuf: fundamentals_str = fundamentals_obj.SerializeToString()
        fundamentals_str = repr(fundamentals_obj)

        if fundamentals_str not in seen_fundamentals:
            seen_fundamentals.add(fundamentals_str)
            unique_records.append(item)

    return unique_records


def sort_by_date_desc(resp):
    # Сортируем по полю "date" в порядке убывания
    return sorted(resp, key=lambda x: x['date'], reverse=True)
