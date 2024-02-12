from tinkoff.invest import Client, InstrumentIdType
from tinkoff.invest.constants import INVEST_GRPC_API
from const import TOKEN
import pprint
from db import instruments
from db import prices

pp = pprint.PrettyPrinter(indent=2)


def update_instruments():
    instruments.init_table()

    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        for i in client.instruments.get_favorites().favorite_instruments:
            instrument = client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=i.figi
            ).instrument

            last_prices_resp = client.market_data.get_last_prices(instrument_id=[i.figi]).last_prices[0].price
            last_price = float(str(last_prices_resp.units)+'.'+str(last_prices_resp.nano))

            pp.pprint(i.ticker)
            pp.pprint(last_price)

            db_instrument = instruments.get_instrument(figi=instrument.figi)

            if not len(db_instrument):
                instruments.insert_instrument(figi=instrument.figi, ticker=instrument.ticker, name=instrument.name)

            # foundamentals = client.instruments.get_asset_fundamentals(
            #     request=GetAssetFundamentalsRequest([instrument.ticker])
            # )


def show_instruments():
    for i in instruments.get_instruments():
        print(i)


def update_prices():
    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        prices.init_table()

        for i in instruments.get_instruments():
            figi = i[0]
            last_prices_resp = client.market_data.get_last_prices(instrument_id=[figi]).last_prices[0].price
            last_price = float(str(last_prices_resp.units)+'.'+str(last_prices_resp.nano))

            print(last_price)
            prices.insert_price(figi=figi, price=last_price)


def show_prices():
    for i in prices.get_prices():
        print(i)


# update_instruments()
# show_instruments()
# update_prices()
show_prices()
