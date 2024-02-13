import datetime

from tinkoff.invest import Client, GetAssetFundamentalsRequest, StatisticResponse, FavoriteInstrument, CandleInterval
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.services import Services
from const import TOKEN


def collect():
    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        favorites = client.instruments.get_favorites().favorite_instruments
        # fundamentals = get_fundamentals(client=client, favorites=favorites)
        #
        # for i in fundamentals:
        #     print(i)

        get_history(client=client, favorites=favorites)


def get_fundamentals(client: Services, favorites: list[FavoriteInstrument]) -> list[StatisticResponse]:
    fundamentals: list[StatisticResponse] = []

    for favorite in favorites:
        try:
            resp = client.instruments.get_asset_fundamentals(
                request=GetAssetFundamentalsRequest(
                    assets=[favorite.uid]
                )
            )

            for f in resp.fundamentals:
                fundamentals.append(f)

        except Exception:
            print('ERROR GETTING FUNDAMENTALS OF:', favorite.ticker)

    return fundamentals


def get_history(client: Services, favorites: list[FavoriteInstrument]):
    for favorite in favorites:
        try:
            resp = client.market_data.get_candles(
                instrument_id=favorite.uid,
                from_=(datetime.datetime.now() - datetime.timedelta(days=365)),
                to=datetime.datetime.now(),
                interval=CandleInterval.CANDLE_INTERVAL_DAY
            )

            for c in resp.candles:
                print(c)

        except Exception:
            print('ERROR GETTING HISTORY OF:', favorite.ticker)
