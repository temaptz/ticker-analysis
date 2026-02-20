import time
import datetime
from lib import predictions, logger, date_utils, instruments, learn, predictions_cache, utils


def finish_log(time_total: float, last_date: datetime.datetime):
    total_hours = time_total / 3600
    if total_hours >= 24:
        days = total_hours // 24
        hours = total_hours % 24
        time_str = f"{int(days)} days {hours:.2f} hours"
    else:
        time_str = f"{total_hours:.2f} hours"

    logger.log_info(
        message='Прогнозы обновлены. Запуск нового цикла прогнозов.',
        output={
            'time': time_str,
            'last_date': last_date,
        },
        is_send_telegram=True,
    )


def refresh_cache_loop(finish_date: datetime.datetime):
    while True:
        logger.log_info(
            message='START REFRESH PREDICTIONS CACHE',
            output={
                'finish_date': finish_date,
            },
            is_send_telegram=False,
        )

        try:
            time_start = time.perf_counter()
            now = date_utils.get_day_prediction_time()
            last_date = now+datetime.timedelta(days=365*1.5)

            for date_target in date_utils.get_dates_interval_list(
                date_from=(now+datetime.timedelta(days=1)),
                date_to=last_date,
                is_order_descending=False,
            ):
                for instrument in instruments.get_instruments_white_list():
                    for model_name in [
                        learn.model.TA_2_1,
                        learn.model.TA_3_tech,
                    ]:
                        if (prediction := predictions.get_prediction(
                                instrument_uid=instrument.uid,
                                model_name=model_name,
                                date_target=date_target,
                                is_ignore_cache=True,
                        )) is not None and -3 <= prediction <= 3:
                            predictions_cache.set_prediction_cache(
                                instrument_uid=instrument.uid,
                                model_name=model_name,
                                date_target=date_target,
                                prediction=utils.round_float(prediction, 10),
                            )

                        logger.log_info(
                            message=f'TARGET_DATE: |{date_target}| TICKER: [{instrument.ticker}] MODEL: {{{model_name}}} PREDICTION: <{prediction if (prediction or prediction == 0) else None}>',
                            is_send_telegram=False,
                        )

                        if datetime.datetime.now(tz=datetime.timezone.utc) >= finish_date:
                            finish_log(time_total=(time.perf_counter() - time_start), last_date=date_target)
                            return None

            finish_log(time_total=(time.perf_counter() - time_start), last_date=last_date)
        except Exception as e:
            logger.log_error(method_name='refresh_cache_loop', error=e)

        time.sleep(3600)


# 3:00 UTC следующего рабочего дня
def get_next_work_day_beginning() -> datetime.datetime:
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    next_day = now + datetime.timedelta(days=1)
    
    # Skip weekends (Monday=0, Sunday=6)
    while next_day.weekday() >= 5:  # 5=Saturday, 6=Sunday
        next_day += datetime.timedelta(days=1)
        
    # Set time to 03:00 UTC
    return next_day.replace(hour=3, minute=0, second=0, microsecond=0)


def predict_infinite_loop():
    while True:
        next_start = get_next_work_day_beginning()
        refresh_cache_loop(finish_date=next_start)
        time.sleep(max(0.0, (next_start - datetime.datetime.now(tz=datetime.timezone.utc)).total_seconds()))

predict_infinite_loop()
