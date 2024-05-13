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
import prices
from const import TOKEN
from db import forecasts
from tinkoff.invest.schemas import GetForecastResponse


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
                        price0 = prices.get_price_by_date(client=client, uid=favorite.uid, date=date0)
                        price1 = prices.get_price_by_date(client=client, uid=favorite.uid, date=date1)
                        price2 = prices.get_price_by_date(client=client, uid=favorite.uid, date=date2)
                        price3 = prices.get_price_by_date(client=client, uid=favorite.uid, date=date3)
                        price4 = prices.get_price_by_date(client=client, uid=favorite.uid, date=date4)
                        price5 = prices.get_price_by_date(client=client, uid=favorite.uid, date=date5)
                        price_target = prices.get_price_by_date(client=client, uid=favorite.uid, date=date_target)

                        if price0 and price1 and price2 and price3 and price4 and price5 and date0 and consensus_price:
                            if date_target and price_target:
                                ent = entity.EntityResolved(
                                    date=date0,
                                    price0=price0,
                                    price1=price1,
                                    price2=price2,
                                    price3=price3,
                                    price4=price4,
                                    price5=price5,
                                    prediction=consensus_price,
                                    result=price_target,
                                    market_capitalization=fundamentals.market_capitalization,
                                    high_price_last_52_weeks=fundamentals.high_price_last_52_weeks,
                                    low_price_last_52_weeks=fundamentals.low_price_last_52_weeks,
                                    average_daily_volume_last_10_days=fundamentals.average_daily_volume_last_10_days,
                                    average_daily_volume_last_4_weeks=fundamentals.average_daily_volume_last_4_weeks,
                                    revenue_ttm=fundamentals.revenue_ttm,
                                    ebitda_ttm=fundamentals.ebitda_ttm,
                                    net_income_ttm=fundamentals.net_income_ttm,
                                    free_cash_flow_ttm=fundamentals.free_cash_flow_ttm,
                                    total_enterprise_value_mrq=fundamentals.total_enterprise_value_mrq,
                                    net_margin_mrq=fundamentals.net_margin_mrq,
                                    total_debt_mrq=fundamentals.total_debt_mrq,
                                    current_ratio_mrq=fundamentals.current_ratio_mrq,
                                    one_year_annual_revenue_growth_rate=fundamentals.one_year_annual_revenue_growth_rate
                                )
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

