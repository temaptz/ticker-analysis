import datetime
from lib import predictions, telegram, instruments, date_utils
from lib.db_2 import predictions_db
from lib.learn import ta_1_2, ta_2, ta_2_1, const


def save_daily_predictions():
    save_predictions_ta_1()
    save_predictions_ta_1_1()


def save_weekly_predictions():
    save_predictions(model_name=const.TA_1_2)
    save_predictions(model_name=const.TA_2)
    save_predictions(model_name=const.TA_2_1)


def save_predictions_ta_1():
    telegram.send_message('Начато сохранение предсказаний модели ta-1')

    counter = 0

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)
        print(instrument.name)

        prediction = predictions.get_prediction_ta_1_by_uid(uid=instrument.uid)

        if prediction:
            print('PREDICTION TA-1: ', prediction)

            predictions_db.insert_prediction(
                instrument_uid=instrument.uid,
                prediction=prediction,
                target_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
                model_name=const.TA_1,
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

            predictions_db.insert_prediction(
                instrument_uid=instrument.uid,
                prediction=prediction,
                target_date=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=30),
                model_name=const.TA_1_1,
            )

            counter += 1

    telegram.send_message('Всего сохранено '+str(counter)+' предсказаний модели ta-1_1')


def save_predictions(model_name: str):
    telegram.send_message(f'Начато сохранение предсказаний модели {model_name}')
    date_today = datetime.datetime.now(datetime.timezone.utc).replace(minute=0, second=0, microsecond=0)
    date_to = date_today + datetime.timedelta(days=365)

    counter = 0

    for instrument in instruments.get_instruments_white_list():
        print(instrument.ticker)

        for date in date_utils.get_dates_interval_list(
                date_from=date_today,
                date_to=date_to,
                interval_seconds=3600 * 24 * 7
        ):
            prediction = ta_2_1.predict_future(instrument_uid=instrument.uid, date_target=date)

            if prediction is not None:
                print(f'PREDICTION {model_name}: ', prediction, date)

                predictions_db.insert_prediction(
                    instrument_uid=instrument.uid,
                    prediction=prediction,
                    target_date=date,
                    model_name=model_name
                )

                counter += 1

    telegram.send_message(f'Всего сохранено {counter} предсказаний модели {model_name}')
