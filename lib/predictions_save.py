from lib import predictions, telegram, instruments
from lib.db_2 import predictions_ta_1_db
from lib.db_2 import predictions_ta_1_1_db


def save_predictions():
    save_predictions_ta_1()
    save_predictions_ta_1_1()


def save_predictions_ta_1():
    telegram.send_message('Начато сохранение предсказаний модели ta-1')

    counter = 0

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        print(instrument.name)

        prediction = predictions.get_prediction_ta_1_by_uid(uid=instrument.uid)

        if prediction:
            print('PREDICTION TA-1: ', prediction)

            predictions_ta_1_db.insert_prediction(
                uid=instrument.uid,
                prediction=prediction
            )

            counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' предсказаний модели ta-1')


def save_predictions_ta_1_1():
    telegram.send_message('Начато сохранение предсказаний модели ta-1_1')

    counter = 0

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        print(instrument.name)

        prediction = predictions.get_prediction_ta_1_1_by_uid(uid=instrument.uid)

        if prediction:
            print('PREDICTION TA-1_1: ', prediction)

            predictions_ta_1_1_db.insert_prediction(
                uid=instrument.uid,
                prediction=prediction
            )

            counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' предсказаний модели ta-1_1')
