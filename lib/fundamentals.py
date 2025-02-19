import datetime
from tinkoff.invest import (
    Client,
    constants,
)
from tinkoff.invest.schemas import GetAssetFundamentalsResponse, GetAssetFundamentalsRequest
from lib.db import fundamentals_db
from const import TINKOFF_INVEST_TOKEN


def get_fundamentals_by_asset_uid(asset_uid: str) -> GetAssetFundamentalsResponse.fundamentals:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_asset_fundamentals(
                request=GetAssetFundamentalsRequest(
                    assets=[asset_uid]
                )
            ).fundamentals

    except Exception as e:
        print('ERROR get_instrument_fundamentals_by_asset_uid', asset_uid, e)


def get_db_fundamentals_by_asset_uid(asset_uid: str, date: datetime.datetime) -> (str, GetAssetFundamentalsResponse.fundamentals, str):
    db_data = fundamentals_db.get_fundamentals_by_asset_uid(asset_uid, date=date)
    asset_uid = db_data[0]
    date = db_data[2]
    fundamentals = fundamentals_db.deserialize(db_data[1])

    return asset_uid, fundamentals, date
