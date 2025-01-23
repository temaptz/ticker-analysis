import tinkoff.invest
from lib.db import forecasts_db


def get_db_forecasts_by_uid(uid: str) -> (str, tinkoff.invest.schemas.GetForecastResponse, str):
    result = list()

    for f in forecasts_db.get_forecasts_by_uid(uid):
        uid = f[0]
        date = f[2]
        forecast = forecasts_db.deserialize(f[1])

        result.append((uid, forecast, date))

    return result
