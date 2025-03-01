from tinkoff.invest import Client, CandleInterval, constants, InstrumentIdType, InstrumentResponse
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
    with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_favorites().favorite_instruments


@cache.ttl_cache(ttl=3600 * 24 * 7)
def get_instrument_by_uid(uid: str):
    with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
            id=uid
        ).instrument


@cache.ttl_cache(ttl=3600 * 24 * 7)
def get_instrument_by_ticker(ticker: str) -> InstrumentResponse.instrument:
    print('GET BY TICKER', ticker)
    with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
            id=ticker,
            class_code='TQBR'
        ).instrument


@cache.ttl_cache(ttl=3600)
def get_instrument_last_price_by_uid(uid: str):
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_last_prices(
                instrument_id=[uid]
            ).last_prices

    except Exception:
        print('ERROR get_instrument_last_price_by_uid')


@cache.ttl_cache(ttl=3600 * 4)
def get_instrument_history_price_by_uid(uid: str, days_count: int, interval: CandleInterval, to_date: datetime.datetime):
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_candles(
                instrument_id=uid,
                from_=(to_date - datetime.timedelta(days=days_count)),
                to=to_date,
                interval=interval
            ).candles

    except Exception:
        print('ERROR get_instrument_history_price_by_uid')
