import time
import datetime
from lib import predictions, logger, date_utils, instruments, learn, predictions_cache, utils

def refresh_cache_loop():
    while True:
        logger.log_info(message='START REFRESH PREDICTIONS CACHE', is_send_telegram=False)

        try:
            time_start = time.perf_counter()
            now = date_utils.get_day_prediction_time()

            for date_target in date_utils.get_dates_interval_list(
                date_from=(now+datetime.timedelta(days=1)),
                date_to=(now+datetime.timedelta(days=365*3)),
                is_order_descending=False,
            ):
                for instrument in instruments.get_instruments_white_list():
                    for model_name in [
                        learn.model.TA_1,
                        learn.model.TA_1_1,
                        learn.model.TA_1_2,
                        learn.model.TA_2,
                        learn.model.TA_2_1,
                        learn.model.CONSENSUS,
                    ]:
                        if (prediction := predictions.get_prediction(
                                instrument_uid=instrument.uid,
                                model_name=model_name,
                                date_target=date_target,
                                avg_days=3,
                                is_ignore_cache=True,
                        )) is not None:
                            predictions_cache.set_prediction_cache(
                                instrument_uid=instrument.uid,
                                model_name=model_name,
                                date_target=date_target,
                                prediction=prediction,
                            )
                            logger.log_info(
                                message=f'TARGET_DATE: |{date_target}| TICKER: [{instrument.ticker}] MODEL: {{{model_name}}} PREDICTION: <{utils.round_float(prediction, 4)}>',
                                is_send_telegram=False,
                            )
            logger.log_info(message='SUCCESS FINIS REFRESH PREDICTIONS CACHE', is_send_telegram=False)

            logger.log_info(
                message=f'REFRESH PREDICTIONS CACHE TIME: {time.strftime("%H:%M:%S", time.gmtime(time.perf_counter() - time_start))}',
                is_send_telegram=True,
            )
        except Exception as e:
            logger.log_error(method_name='refresh_cache_loop', error=e)

        time.sleep(3600)

refresh_cache_loop()
