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
import predictions_db
import predictions


def save_favorite_predictions():
    predictions_db.init_table()

    with Client(TOKEN, target=INVEST_GRPC_API) as client:
        favorites = client.instruments.get_favorites().favorite_instruments

        for favorite in favorites:
            print(favorite.ticker)
            print(favorite.name)

            prediction = predictions.get_prediction_by_uid(favorite.uid)
            if prediction:
                print('PREDICTION', prediction)

                predictions_db.insert_prediction(
                    uid=favorite.uid,
                    prediction=prediction
                )
