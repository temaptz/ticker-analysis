from tinkoff.invest import Client
from tinkoff.invest.constants import INVEST_GRPC_API

import utils
from const import TOKEN
from db import instruments
from db import prices
from tinkoff.invest.services import Services
import datetime
from tinkoff.invest import (
    Client,
    CandleInterval,
)


def update_prices():
    prices.init_table()

    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        for i in instruments.get_instruments():
            figi = i[0]
            last_prices_resp = client.market_data.get_last_prices(instrument_id=[figi]).last_prices[0].price
            last_price = float(str(last_prices_resp.units)+'.'+str(last_prices_resp.nano))

            print(last_price)
            prices.insert_price(figi=figi, price=last_price)


def show_prices():
    for i in prices.get_prices():
        print(i)


def get_price_by_date(client: Services, uid: str, date: datetime) -> float:
    try:
        time_from = datetime.datetime.replace(date, hour=0, minute=0, second=0, microsecond=0)
        time_to = datetime.datetime.replace(date, hour=23, minute=59, second=59, microsecond=999999)

        resp = client.market_data.get_candles(
            instrument_id=uid,
            from_=time_from,
            to=time_to,
            interval=CandleInterval.CANDLE_INTERVAL_DAY
        )

        return utils.get_price_by_quotation(resp.candles[0].close)

    except Exception:
        print('ERROR GETTING PRICE BY DATE', date)
        return None
