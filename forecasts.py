from tinkoff.invest import (
    Client,
    FavoriteInstrument,
)
from tinkoff.invest.schemas import (
    GetForecastResponse,
    GetForecastRequest,
)
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.services import Services
from const import TOKEN
from db import forecasts


def save_favorite_forecasts():
    forecasts.init_table()

    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        favorites = client.instruments.get_favorites().favorite_instruments

        for favorite in favorites:
            print(favorite.ticker)
            print(favorite.name)

            f = get_forecasts(client=client, favorite=favorite)
            if f:
                print('FORECASTS')
                for i in f.targets:
                    print(i)

                print('CONSENSUS FORECASTS')
                print(f.consensus)

                forecasts.insert_forecast(
                    uid=favorite.uid,
                    forecast=forecasts.serialize(f)
                )


def show_saved_forecasts():
    for f in forecasts.get_forecasts():
        uid = f[0]
        date = f[2]
        data = forecasts.deserialize(f[1])
        print(uid)
        print(date)
        print(data)


def get_forecasts(client: Services, favorite: FavoriteInstrument) -> GetForecastResponse:
    try:
        return client.instruments.get_forecast_by(
            request=GetForecastRequest(
                instrument_id=favorite.uid
            )
        )

    except Exception:
        print('ERROR GETTING FORECASTS OF:', favorite.ticker)
