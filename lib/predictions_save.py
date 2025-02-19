from lib import predictions, telegram, instruments
from lib.db import predictions_ta_1_db


def save_predictions():
    telegram.send_message('Начато сохранение предсказаний нейросети')

    counter = 0

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        print(instrument.name)

        prediction = predictions.get_prediction_ta_1_by_uid(instrument.uid)

        if prediction:
            print('PREDICTION: ', prediction)

            predictions_db.insert_prediction(
                uid=instrument.uid,
                prediction=prediction
            )

            counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' предсказаний нейросети')
