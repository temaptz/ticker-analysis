from tinkoff.invest import (
    Client,
    StatisticResponse,
    FavoriteInstrument,
    CandleInterval,
    HistoricCandle,
    constants,
)
import os
import sys

root_directory = os.path.abspath('../')
sys.path.append(root_directory)
from const import TOKEN


def get_favorites():
    with Client(TOKEN, target=constants.INVEST_GRPC_API) as client:
        favorites = client.instruments.get_favorites().favorite_instruments

        return favorites
