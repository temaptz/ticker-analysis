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
from lib.db import forecasts_db
from lib import telegram


def save_favorite_forecasts():
    telegram.send_message('Начато сохранение прогнозов аналитиков')

    counter = 0

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

                forecasts_db.insert_forecast(
                    uid=favorite.uid,
                    forecast=forecasts_db.serialize(f)
                )

                counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' прогнозов аналитиков')


def show_saved_forecasts():
    for f in forecasts_db.get_forecasts():
        uid = f[0]
        date = f[2]
        data = forecasts_db.deserialize(f[1])
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
