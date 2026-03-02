from lib import logger, learn, cache


@cache.ttl_cache(ttl=3600 * 24, is_skip_empty=True, cache_salt='_')
def get_volume_buy_rate(instrument_uid: str):
    final_rate = 0
    prediction = None

    try:
        prediction = learn.ta_3_volume_learn.predict_future(instrument_uid=instrument_uid)

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


@cache.ttl_cache(ttl=3600 * 24, is_skip_empty=True, cache_salt='_')
def get_volume_sell_rate(instrument_uid: str):
    final_rate = 0
    prediction = None

    try:
        prediction = learn.ta_3_volume_learn.predict_future(instrument_uid=instrument_uid)

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
