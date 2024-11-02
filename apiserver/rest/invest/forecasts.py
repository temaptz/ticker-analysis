import datetime
import tinkoff.invest
import os
import sys
from serializer import get_dict_by_object
import forecasts_db
from const import TOKEN


def get_db_forecasts_by_uid(uid: str) -> (str, tinkoff.invest.schemas.GetForecastResponse, str):
    result = list()

    for f in forecasts_db.get_forecasts_by_uid(uid):
        uid = f[0]
        date = f[2]
        forecast = forecasts_db.deserialize(f[1])

        result.append((uid, forecast, date))

    return result
