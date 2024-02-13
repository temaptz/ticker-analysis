from tinkoff.invest import Client
from tinkoff.invest.constants import INVEST_GRPC_API
from const import TOKEN
from db import instruments
from db import prices


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
