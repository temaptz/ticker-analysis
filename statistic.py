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
    Smoothing,
    Quotation,
    IndicatorType,
    IndicatorInterval,
    TypeOfPrice,
    TechAnalysisItem,
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

            # fundamentals = get_fundamentals(client=client, favorite=favorite)
            # print('FUNDAMENTALS')
            # print(fundamentals)
            #
            # history = get_history(client=client, favorite=favorite)
            # print('HISTORY')
            # for i in history:
            #     print(i)
            #
            # f = forecasts.get_forecasts(client=client, favorite=favorite)
            # if f:
            #     print('FORECASTS')
            #     for i in f.targets:
            #         print(i)
            #
            #     print('CONSENSUS FORECASTS')
            #     print(f.consensus)

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


def get_tech_analysis(client: Services, favorite: FavoriteInstrument) -> list[TechAnalysisItem]:
    try:
        resp = client.market_data.get_tech_analysis(
            request=GetTechAnalysisRequest(
                indicator_type=IndicatorType.INDICATOR_TYPE_SMA,
                instrument_uid=favorite.uid,
                from_=(datetime.datetime.now() - datetime.timedelta(days=90)),
                to=datetime.datetime.now(),
                interval=IndicatorInterval.INDICATOR_INTERVAL_WEEK,
                type_of_price=TypeOfPrice.TYPE_OF_PRICE_AVG,
                length=1,
                deviation=Deviation(
                    deviation_multiplier=Quotation(
                        units=1,
                        nano=0
                    )
                ),
                smoothing=Smoothing(
                    fast_length=3,
                    slow_length=1,
                    signal_smoothing=2
                )
            )
        )

        return resp.technical_indicators

    except Exception:
        print('ERROR GETTING TECH ANALYSIS OF:', favorite.ticker)
