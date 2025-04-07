from tinkoff.invest import Client, CandleInterval, constants, InstrumentIdType, InstrumentResponse, HistoricCandle, LastPrice
import datetime
from const import TINKOFF_INVEST_TOKEN, TICKER_LIST
from lib import cache, utils, date_utils


@cache.ttl_cache(ttl=3600 * 24)
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
    with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
            id=ticker,
            class_code='TQBR'
        ).instrument


@cache.ttl_cache(ttl=3600)
def get_instrument_last_price_by_uid(uid: str) -> list[LastPrice] or None:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_last_prices(
                instrument_id=[uid]
            ).last_prices

    except Exception as e:
        print('ERROR get_instrument_last_price_by_uid', e)


@cache.ttl_cache(ttl=3600 * 4)
def get_instrument_history_price_by_uid(uid: str, days_count: int, interval: CandleInterval, to_date: datetime.datetime) -> list[HistoricCandle]:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_candles(
                instrument_id=uid,
                from_=(to_date - datetime.timedelta(days=days_count)),
                to=to_date,
                interval=interval
            ).candles

    except Exception as e:
        print('ERROR get_instrument_history_price_by_uid', e)


@cache.ttl_cache(ttl=3600)
def get_instrument_price_by_date(uid: str, date: datetime.datetime) -> float or None:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            date_local = date_utils.convert_to_local(date=date)
            date_utc = date_utils.convert_to_utc(date=date)
            candles = client.market_data.get_candles(
                instrument_id=uid,
                from_=date_utc - datetime.timedelta(minutes=30),
                to=date_utc + datetime.timedelta(minutes=30),
                interval=CandleInterval.CANDLE_INTERVAL_HOUR
            ).candles

            nearest: HistoricCandle or None = None

            for i in candles:
                time_local = date_utils.convert_to_local(i.time)

                if nearest:
                    delta_sec_i = (date_local - time_local).total_seconds()
                    delta_sec_nearest = (date_local - date_utils.convert_to_local(nearest.time)).total_seconds()

                    if delta_sec_i < delta_sec_nearest:
                        nearest = i
                else:
                    nearest = i

            if nearest:
                return utils.get_price_by_candle(nearest)

    except Exception as e:
        print('ERROR get_instrument_price_by_date', e)

    return None
