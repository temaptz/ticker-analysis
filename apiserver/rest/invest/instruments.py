from tinkoff.invest import (
    Client,
    StatisticResponse,
    FavoriteInstrument,
    CandleInterval,
    HistoricCandle,
    constants,
    InstrumentIdType,
    schemas
)
import os
import sys
import datetime

root_directory = os.path.abspath('../')
sys.path.append(root_directory)
from const import TOKEN


def get_instrument_by_uid(uid: str):
    with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
            id=uid
        ).instrument


def get_favorites():
    with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_favorites().favorite_instruments


def get_instrument_last_price_by_uid(uid: str):
    try:
        with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_last_prices(
                instrument_id=[uid]
            ).last_prices

    except Exception:
        print('ERROR get_instrument_last_price_by_uid')


def get_instrument_history_price_by_uid(uid: str, daysCount: int, interval: CandleInterval):
    try:
        with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_candles(
                instrument_id=uid,
                from_=(datetime.datetime.now() - datetime.timedelta(days=daysCount)),
                to=datetime.datetime.now(),
                interval=interval
            ).candles

    except Exception:
        print('ERROR get_instrument_history_price_by_uid')


def get_instrument_consensus_forecast_by_uid(uid: str):
    try:
        with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_forecast_by(
                request=schemas.GetForecastRequest(
                    instrument_id=uid
                )
            ).consensus

    except Exception:
        print('ERROR get_instrument_consensus_forecast_by_uid')


def get_instrument_fundamentals_by_uid(uid: str):
    try:
        with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_asset_fundamentals(
                request=schemas.GetAssetFundamentalsRequest(
                    assets=[uid]
                )
            ).fundamentals

    except Exception:
        print('ERROR get_instrument_fundamentals_by_uid')
