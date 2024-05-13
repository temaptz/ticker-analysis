import datetime

from tinkoff.invest import (
    Client,
    StatisticResponse,
    FavoriteInstrument,
    CandleInterval,
    HistoricCandle,
)
from tinkoff.invest.schemas import (
    GetAssetFundamentalsRequest,
    GetTechAnalysisRequest,
    Deviation,
    Quotation,
)
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.services import Services
from const import TOKEN
import forecasts


def collect():
    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        favorites = client.instruments.get_favorites().favorite_instruments

        for favorite in favorites:
            print(favorite.ticker)
            print(favorite.name)

            fundamentals = get_fundamentals(client=client, favorite=favorite)
            print('FUNDAMENTALS')
            print(fundamentals)

            history = get_history(client=client, favorite=favorite)
            print('HISTORY')
            for i in history:
                print(i)

            tech = get_tech_analysis(client=client, favorite=favorite)
            print('TECH ANALYSIS')
            print(tech)


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
    try:
        resp = client.market_data.get_tech_analysis(
            request=GetTechAnalysisRequest(
                indicator_type=GetTechAnalysisRequest.indicator_type.INDICATOR_TYPE_SMA,
                instrument_uid=favorite.uid,
                from_=(datetime.datetime.now() - datetime.timedelta(days=90)),
                to=datetime.datetime.now(),
                interval=GetTechAnalysisRequest.interval.INDICATOR_INTERVAL_WEEK,
                type_of_price=GetTechAnalysisRequest.type_of_price.TYPE_OF_PRICE_AVG,
                length=1,
                deviation=Deviation(
                    deviation_multiplier=Quotation(
                        units=1,
                        nano=0
                    )
                ),
                smoothing=Deviation(
                    deviation_multiplier=Quotation(
                        units=0,
                        nano=1
                    )
                )
            )
        )

        return resp

    except Exception:
        print('ERROR GETTING TECH ANALYSIS OF:', favorite.ticker)
