from tinkoff.invest import (
    Client,
)
from tinkoff.invest.constants import INVEST_GRPC_API
from const import TOKEN
from lib.db import predictions_db
from lib import (predictions, telegram)


def save_favorite_predictions():
    telegram.send_message('Начато сохранение предсказаний нейросети')

    counter = 0

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

                counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' предсказаний нейросети')
