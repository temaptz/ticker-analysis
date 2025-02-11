from tinkoff.invest import (
    Client,
    CandleInterval,
    constants,
    InstrumentIdType,
    schemas
)
import datetime
from const import TOKEN
from lib import cache


@cache.ttl_cache(ttl=60)
def get_favorites():
    with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_favorites().favorite_instruments


@cache.ttl_cache()
def get_instrument_by_uid(uid: str):
    with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
            id=uid
        ).instrument


@cache.ttl_cache()
def get_instrument_last_price_by_uid(uid: str):
    try:
        with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_last_prices(
                instrument_id=[uid]
            ).last_prices

    except Exception:
        print('ERROR get_instrument_last_price_by_uid')


@cache.ttl_cache()
def get_instrument_history_price_by_uid(uid: str, days_count: int, interval: CandleInterval, to_date: datetime.datetime):
    try:
        with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_candles(
                instrument_id=uid,
                from_=(to_date - datetime.timedelta(days=days_count)),
                to=to_date,
                interval=interval
            ).candles

    except Exception:
        print('ERROR get_instrument_history_price_by_uid')


@cache.ttl_cache()
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


@cache.ttl_cache()
def get_instrument_fundamentals_by_asset_uid(asset_uid: str):
    try:
        with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_asset_fundamentals(
                request=schemas.GetAssetFundamentalsRequest(
                    assets=[asset_uid]
                )
            ).fundamentals

    except Exception:
        print('ERROR get_instrument_fundamentals_by_uid')
