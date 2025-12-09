import datetime
from lib import predictions, telegram, instruments, date_utils, logger
from lib.db_2 import predictions_db
from lib.learn import model


def save_weekly_predictions():
    save_predictions(model_name=model.TA_2_1)


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
            prediction = predictions.get_prediction_cache(
                instrument_uid=instrument.uid,
                date_target=date,
                model_name=model_name,
                avg_days=5,
            )

            if prediction is not None:
                logger.log_info(f'PREDICTION {model_name}: {prediction}')

                predictions_db.insert_prediction(
                    instrument_uid=instrument.uid,
                    prediction=prediction,
                    target_date=date,
                    model_name=model_name
                )

                counter += 1

    telegram.send_message(f'Всего сохранено {counter} предсказаний модели {model_name}')
