import datetime
from lib import logger, learn, cache, predictions_cache, date_utils
from lib.learn import enum


def get_volume_buy_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    prediction = None

    try:
        if prediction := _get_prediction(instrument_uid=instrument_uid, date=date):
            if prediction == enum.PriceDirection.PRICE_UP.value:
                final_rate = 1
            elif prediction == enum.PriceDirection.PRICE_SAME.value:
                final_rate = 0.3
    except Exception as e:
        logger.log_error(method_name='get_volume_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'prediction': prediction,
        },
    }


def get_volume_sell_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    prediction = None

    try:
        if prediction := _get_prediction(instrument_uid=instrument_uid, date=date):
            if prediction == enum.PriceDirection.PRICE_DOWN.value:
                final_rate = 1
            elif prediction == enum.PriceDirection.PRICE_SAME.value:
                final_rate = 0.3
    except Exception as e:
        logger.log_error(method_name='get_volume_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'prediction': prediction,
        },
    }


@cache.ttl_cache(ttl=3600)
def _get_prediction(instrument_uid: str, date: datetime.datetime or None = None):
    if not date or date_utils.is_same_day(a=date, b=date_utils.get_day_prediction_time()):
        if (cached := predictions_cache.get_classifier_prediction_cache(
            instrument_uid=instrument_uid,
            model_name=learn.model.TA_3_volume,
        )) and cached in [enum.PriceDirection.PRICE_UP.value, enum.PriceDirection.PRICE_SAME.value, enum.PriceDirection.PRICE_DOWN.value]:
            return cached

    return learn.ta_3_volume_learn.predict_future(instrument_uid=instrument_uid, date_current=date)
