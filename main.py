from tinkoff.invest import Client, InstrumentIdType, GetAssetFundamentalsRequest
from tinkoff.invest.constants import INVEST_GRPC_API
from const import TOKEN
import pprint

pp = pprint.PrettyPrinter(indent=2)

with Client(TOKEN, target=INVEST_GRPC_API) as client:
    for i in client.instruments.get_favorites().favorite_instruments:
        # instrument = client.instruments.get_instrument_by(
        #     id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
        #     id=i.figi
        # ).instrument

        last_prices_resp = client.market_data.get_last_prices(instrument_id=[i.figi]).last_prices[0].price
        last_price = float(str(last_prices_resp.units)+'.'+str(last_prices_resp.nano))

        pp.pprint(i.ticker)
        pp.pprint(last_price)

        # foundamentals = client.instruments.get_asset_fundamentals(
        #     request=GetAssetFundamentalsRequest([instrument.ticker])
        # )
