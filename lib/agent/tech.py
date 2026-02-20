import datetime
from lib import date_utils, agent, utils, logger, learn, predictions, cache
from lib.learn.ta_3_technical import TARGET_MAX_DAYS_COUNT


@cache.ttl_cache(ttl=3600)
def get_tech_buy_rate(instrument_uid: str):
    final_rate_value = 0
    target_prediction_value = 0.05
    max_prediction = 0
    max_prediction_date = 0
    days_rates = []
    predictions_list = []
    is_no_predictions = True

    try:
        now = date_utils.get_day_prediction_time(date=datetime.datetime.now(tz=datetime.timezone.utc))
        date_from = now + datetime.timedelta(days=1)
        date_to = now + datetime.timedelta(days=TARGET_MAX_DAYS_COUNT)

        for day in date_utils.get_dates_interval_list(
                date_from=date_from,
                date_to=date_to,
                interval_seconds=(3600 * 24)
        ):
            day_rate = None

            if (pred := predictions.get_prediction(
                    instrument_uid=instrument_uid,
                    date_target=day,
                    model_name=learn.model.TA_3_tech,
            )) or pred == 0:
                is_no_predictions = False

                if 0 < pred < (target_prediction_value * 10):
                    day_rate = agent.utils.linear_interpolation(pred, 0, target_prediction_value, 0, 1)

                    if pred > max_prediction:
                        max_prediction = pred
                        max_prediction_date = day

            predictions_list.append(utils.round_float(pred, 3) if (pred or pred == 0) else None)
            days_rates.append(day_rate)

        final_rate = max(days_rates)

        final_rate_value = 0 if is_no_predictions else max(0, min(final_rate, 1))

    except Exception as e:
        logger.log_error(method_name='rsi_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate_value,
        'debug': {
            'rate': final_rate_value,
            'max_prediction_date': max_prediction_date,
            'max_prediction_value': max_prediction,
            'target_prediction_value': target_prediction_value,
            'predictions': predictions_list,
        },
    }


@cache.ttl_cache(ttl=3600)
def get_tech_sell_rate(instrument_uid: str):
    final_rate_value = 0
    days_before_positive_prediction = None
    predictions_list = []
    is_no_predictions = True

    try:
        now = date_utils.get_day_prediction_time(date=datetime.datetime.now(tz=datetime.timezone.utc))
        date_from = now + datetime.timedelta(days=1)
        date_to = now + datetime.timedelta(days=TARGET_MAX_DAYS_COUNT)

        for day in date_utils.get_dates_interval_list(
                date_from=date_from,
                date_to=date_to,
                interval_seconds=(3600 * 24)
        ):
            pred = predictions.get_prediction(
                instrument_uid=instrument_uid,
                date_target=day,
                model_name=learn.model.TA_3_tech,
            )

            predictions_list.append(utils.round_float(pred or 0, 3))

            if pred:
                is_no_predictions = False

                if pred > 0.005:
                    delta_days = (day - date_from).days
                    if days_before_positive_prediction is None or delta_days < days_before_positive_prediction:
                        days_before_positive_prediction = delta_days

        days_lerp = days_before_positive_prediction if (days_before_positive_prediction is not None) else TARGET_MAX_DAYS_COUNT
        final_rate = agent.utils.linear_interpolation(days_lerp, 0, TARGET_MAX_DAYS_COUNT, 0, 1)

        final_rate_value = 0 if is_no_predictions else max(0, min(final_rate, 1))

    except Exception as e:
        logger.log_error(method_name='price_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate_value,
        'debug': {
            'rate': final_rate_value,
            'days_before_positive': days_before_positive_prediction,
            'predictions': predictions_list,
        },
    }
