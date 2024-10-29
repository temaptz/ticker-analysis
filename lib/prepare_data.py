import datetime
import time

from tinkoff.invest import (
    Client,
    StatisticResponse,
    FavoriteInstrument,
    CandleInterval,
    HistoricCandle,
)
from tinkoff.invest.schemas import (
    GetAssetFundamentalsRequest,
)
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.services import Services

import const
import entity
import utils
from const import TOKEN
from db import forecasts_db
from learning_card import LearningCard
from tinkoff.invest.schemas import GetForecastResponse


def prepare_cards():
    forecast_days = 30
    i = 0
    j = 0

    for uid in get_uids():
        for day in get_days(days=365, offset_days=forecast_days):
            print(i, uid, day)
            c = LearningCard(
                uid=uid,
                date=day,
                target_forecast_days=forecast_days
            )

            c.print_card()

            if c.is_ok:
                j += 1

            i += 1

            print('('+str(j)+' / '+str(i)+')')

    # c = LearningCard(
    #     uid='ca845f68-6c43-44bc-b584-330d2a1e5eb7',
    #     date=(datetime.datetime.now() - datetime.timedelta(days=30)),
    #     target_forecast_days=forecast_days
    # )
    # c.print_card()


def get_uids() -> list[str]:
    result = list[str]()

    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        for i in client.instruments.get_favorites().favorite_instruments:
            result.append(i.uid)

    return result


def get_days(days: int, offset_days: int) -> list[datetime.datetime]:
    result = list[datetime.datetime]()
    end_date = datetime.datetime.now() - datetime.timedelta(days=offset_days)

    for i in range(0, days):
        date = end_date - datetime.timedelta(days=i)
        result.append(date)

    return result


def show():
    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        favorites = client.instruments.get_favorites().favorite_instruments
        iterator = 0

        for favorite in favorites:
            fundamentals = get_fundamentals(client=client, favorite=favorite)

            if fundamentals:
                print(favorite.ticker)
                print(favorite.name)
                time.sleep(1)

                for f in forecasts.get_forecasts_by_uid(favorite.uid):
                    forecast_response: GetForecastResponse = forecasts.deserialize(f[1])
                    consensus_price = utils.get_price_by_quotation(forecast_response.consensus.consensus)
                    date0 = datetime.datetime.fromisoformat(f[2])
                    date1 = date0 - datetime.timedelta(weeks=1)
                    date2 = date0 - datetime.timedelta(weeks=2)
                    date3 = date0 - datetime.timedelta(weeks=3)
                    date4 = date0 - datetime.timedelta(weeks=4)
                    date5 = date0 - datetime.timedelta(weeks=5)
                    date_target = date0 + datetime.timedelta(hours=const.TIME_DELTA_HOURS)

                    if date_target <= datetime.datetime.now():
                                iterator += 1
                                print(iterator)
                                ent.display()
                                print(fundamentals)
            else:
                print('NO FUNDAMENTALS', favorite.ticker)









        #
        #     fundamentals = get_fundamentals(client=client, favorite=favorite)
        #     print('FUNDAMENTALS')
        #     print(fundamentals)
        #
        #     history = get_history(client=client, favorite=favorite)
        #     print('HISTORY')
        #     for i in history:
        #         print(i)
        #
        #     f = forecasts.get_forecasts(client=client, favorite=favorite)
        #     if f:
        #         print('FORECASTS')
        #         for i in f.targets:
        #             print(i)
        #
        #         print('CONSENSUS FORECASTS')
        #         print(f.consensus)


def get_fundamentals(client: Services, favorite: FavoriteInstrument) -> StatisticResponse:
    try:
        resp = client.instruments.get_asset_fundamentals(
            request=GetAssetFundamentalsRequest(
                assets=[favorite.uid]
            )
        )

        return resp.fundamentals[0]

    except Exception:
        print('ERROR GETTING FUNDAMENTALS OF:', favorite.ticker)


def get_history(client: Services, favorite: FavoriteInstrument) -> list[HistoricCandle]:
    candles: list[HistoricCandle] = []

    try:
        resp = client.market_data.get_candles(
            instrument_id=favorite.uid,
            from_=(datetime.datetime.now() - datetime.timedelta(days=365)),
            to=datetime.datetime.now(),
            interval=CandleInterval.CANDLE_INTERVAL_DAY
        )

        for c in resp.candles:
            candles.append(c)

    except Exception:
        print('ERROR GETTING HISTORY OF:', favorite.ticker)

    return candles


def get_tech_analysis(client: Services, favorite: FavoriteInstrument) -> None:
    return None

