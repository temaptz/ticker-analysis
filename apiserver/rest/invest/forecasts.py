import datetime
import tinkoff.invest
import os
import sys
from .serializer import get_dict_by_object

root_directory = os.path.abspath('../')
sys.path.append(root_directory)
from db import forecasts


def get_forecasts(uid: str) -> (str, tinkoff.invest.schemas.GetForecastResponse, str):
    result = list()

    for f in forecasts.get_forecasts_by_uid(uid):
        uid = f[0]
        date = f[2]
        forecast = forecasts.deserialize(f[1])

        result.append((uid, forecast, date))

    return result
