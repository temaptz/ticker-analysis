from tinkoff.invest import (
    Client,
    CandleInterval,
    constants,
    InstrumentIdType,
    schemas,
    InstrumentResponse
)
import datetime
from const import TINKOFF_INVEST_TOKEN, TICKER_LIST
from lib import cache


@cache.ttl_cache()
def get_instruments_white_list() -> list[InstrumentResponse.instrument]:
    result = list()

    for ticker in TICKER_LIST:
        instrument = get_instrument_by_ticker(ticker=ticker)

        if instrument:
            result.append(instrument)

    return result


@cache.ttl_cache(ttl=60)
def get_favorites():
    with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_favorites().favorite_instruments


@cache.ttl_cache()
def get_instrument_by_uid(uid: str):
    with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
            id=uid
        ).instrument


@cache.ttl_cache()
def get_instrument_by_ticker(ticker: str) -> InstrumentResponse.instrument:
    with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
            id=ticker,
            class_code='TQBR'
        ).instrument


@cache.ttl_cache()
def get_instrument_last_price_by_uid(uid: str):
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_last_prices(
                instrument_id=[uid]
            ).last_prices

    except Exception:
        print('ERROR get_instrument_last_price_by_uid')


@cache.ttl_cache()
def get_instrument_history_price_by_uid(uid: str, days_count: int, interval: CandleInterval, to_date: datetime.datetime):
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
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
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_forecast_by(
                request=schemas.GetForecastRequest(
                    instrument_id=uid
                )
            ).consensus

    except Exception as e:
        print('ERROR get_instrument_consensus_forecast_by_uid', uid, e)


@cache.ttl_cache()
def get_instrument_fundamentals_by_asset_uid(asset_uid: str):
    try:
        with Client(TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_asset_fundamentals(
                request=schemas.GetAssetFundamentalsRequest(
                    assets=[asset_uid]
                )
            ).fundamentals

    except Exception as e:
        print('ERROR get_instrument_fundamentals_by_uid', asset_uid, e)
