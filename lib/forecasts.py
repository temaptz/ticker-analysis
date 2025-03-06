import datetime
from tinkoff.invest import Client, constants
from tinkoff.invest.schemas import GetForecastResponse, GetForecastRequest
from lib.db import forecasts_db
from const import TINKOFF_INVEST_TOKEN
from lib import cache


@cache.ttl_cache(ttl=3600 * 24 * 3)
def get_forecasts(instrument_uid: str) -> GetForecastResponse:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            return client.instruments.get_forecast_by(
                request=GetForecastRequest(
                    instrument_id=instrument_uid
                )
            )

    except Exception as e:
        print('ERROR GETTING FORECASTS OF: ', instrument_uid, e)


@cache.ttl_cache(ttl=3600 * 24 * 3)
def get_db_forecasts_by_uid(uid: str) -> (str, GetForecastResponse, str):
    result = list()

    for f in forecasts_db.get_forecasts_by_uid(uid):
        uid = f[0]
        date = f[2]
        forecast = forecasts_db.deserialize(f[1])

        result.append((uid, forecast, date))

    return result


@cache.ttl_cache(ttl=3600 * 24 * 3)
def get_db_forecast_by_uid_date(uid: str, date: datetime.datetime) -> (str, GetForecastResponse, str):
    db_resp = forecasts_db.get_forecast_by_uid_date(uid=uid, date=date)
    uid = db_resp[0]
    date = db_resp[2]
    forecast = forecasts_db.deserialize(db_resp[1])

    return uid, forecast, date
