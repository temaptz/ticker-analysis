import datetime
from lib import logger, learn, cache, predictions_cache


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_volume_buy_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    prediction = None

    try:
        prediction = _get_prediction(instrument_uid=instrument_uid, date=date)

        if prediction == 'upper':
            final_rate = 1
        elif prediction == 'same':
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


@cache.ttl_cache(ttl=3600, is_skip_empty=True)
def get_volume_sell_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    prediction = None

    try:
        prediction = _get_prediction(instrument_uid=instrument_uid, date=date)

        if prediction == 'lower':
            final_rate = 1
        elif prediction == 'same':
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

def _get_prediction(instrument_uid: str, date: datetime.datetime or None = None):
    if not date:
        if (cached := predictions_cache.get_prediction_cache(
            instrument_uid=instrument_uid,
            model_name=learn.model.TA_3_volume,
        )) and cached:
            return cached

    return learn.ta_3_volume_learn.predict_future(instrument_uid=instrument_uid, date_current=date)
