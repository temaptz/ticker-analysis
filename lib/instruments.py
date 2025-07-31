from typing import Optional

from tinkoff.invest import Client, CandleInterval, constants, InstrumentIdType, HistoricCandle, Instrument
import datetime
from const import TINKOFF_INVEST_TOKEN, TICKER_LIST
from lib import cache, utils, date_utils, db_2, yandex


@cache.ttl_cache(ttl=3600 * 24, is_convert_object=True, is_skip_empty=True)
def get_instruments_white_list() -> list[Instrument]:
    result = list()

    for ticker in TICKER_LIST:
        instrument = get_instrument_by_ticker(ticker=ticker)

        if instrument:
            result.append(instrument)

    return result


@cache.ttl_cache(ttl=3600 * 24 * 10, is_convert_object=True, is_skip_empty=True)
def get_instrument_by_uid(uid: str) -> Instrument:
    with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID,
            id=uid
        ).instrument


@cache.ttl_cache(ttl=3600 * 24 * 10, is_convert_object=True, is_skip_empty=True)
def get_instrument_by_ticker(ticker: str) -> Instrument:
    with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.instruments.get_instrument_by(
            id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
            id=ticker,
            class_code='TQBR'
        ).instrument


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_instrument_last_price_by_uid(uid: str) -> float or None:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            last_prices = client.market_data.get_last_prices(
                instrument_id=[uid]
            ).last_prices

            if last_prices and len(last_prices) > 0 and last_prices[0].price:
                if price := utils.get_price_by_quotation(last_prices[0].price):
                    return price

    except Exception as e:
        print('ERROR get_instrument_last_price_by_uid', e)

    return None


@cache.ttl_cache(ttl=3600 * 4, is_skip_empty=True)
def get_instrument_history_price_by_uid(uid: str, days_count: int, interval: CandleInterval, to_date: datetime.datetime) -> list[HistoricCandle]:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.market_data.get_candles(
                instrument_id=uid,
                from_=(to_date - datetime.timedelta(days=days_count)),
                to=to_date,
                interval=interval
            ).candles or []

    except Exception as e:
        print('ERROR get_instrument_history_price_by_uid', e)


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_instrument_price_by_date(uid: str, date: datetime.datetime, delta_hours=24) -> float or None:
    if date.date() == datetime.datetime.now().date():
        return get_instrument_last_price_by_uid(uid=uid)

    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            date_local = date_utils.convert_to_local(date=date)
            date_utc = date_utils.convert_to_utc(date=date)
            candles = client.market_data.get_candles(
                instrument_id=uid,
                from_=date_utc - datetime.timedelta(hours=delta_hours),
                to=date_utc + datetime.timedelta(hours=delta_hours),
                interval=(CandleInterval.CANDLE_INTERVAL_HOUR if delta_hours < 48 else CandleInterval.CANDLE_INTERVAL_DAY)
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


@cache.ttl_cache(ttl=3600 * 24 * 10, is_skip_empty=True)
def get_instrument_human_name(uid: str) -> Optional[str]:
    tag_name= 'human_name'

    if tag := db_2.instrument_tags_db.get_tag(instrument_uid=uid, tag_name=tag_name):
        if tag_value := tag.tag_value:
            if isinstance(tag_value, str):
                return tag_value

    if instrument := get_instrument_by_uid(uid=uid):
        if yandex_value := yandex.get_human_name(legal_name=instrument.name):
            db_2.instrument_tags_db.upset_tag(
                instrument_uid=uid,
                tag_name=tag_name,
                tag_value=yandex_value,
            )

            return yandex_value

        if instrument.name:
            return instrument.name

    return None


@cache.ttl_cache(ttl=3600 * 24 * 10, is_skip_empty=True)
def get_instrument_keywords(uid: str) -> list[str]:
    tag_name= 'keywords'
    tag_join_symbol = ','

    if tag := db_2.instrument_tags_db.get_tag(instrument_uid=uid, tag_name=tag_name):
        if tag_value := tag.tag_value:
            if isinstance(tag_value, str):
                tag_list = [i for i in tag_value.split(tag_join_symbol) if i]
                if tag_list and len(tag_list) > 0:
                    return tag_list

    if instrument := get_instrument_by_uid(uid=uid):
        if yandex_value := yandex.get_keywords(legal_name=instrument.name):
            if yandex_value and len(yandex_value) > 0:
                db_2.instrument_tags_db.upset_tag(
                    instrument_uid=uid,
                    tag_name=tag_name,
                    tag_value=tag_join_symbol.join(yandex_value),
                )
                return yandex_value
    return []
