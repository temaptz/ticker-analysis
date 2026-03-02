from lib import logger, predictions_cache, learn, agent, cache


@cache.ttl_cache(ttl=(3600 * 24), is_skip_empty=True)
def get_fundamental_buy_rate(instrument_uid: str):
    final_rate = 0
    prediction = 0

    try:
        if (prediction := predictions_cache.get_prediction_cache(
            instrument_uid=instrument_uid,
            model_name=learn.model.TA_3_fundamental,
        )) and prediction > 0:
            rate = agent.utils.linear_interpolation(prediction, 0, 0.2, 0, 1)
            final_rate = min(rate, 1)

    except Exception as e:
        logger.log_error(method_name='get_fundamental_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'prediction': prediction,
        },
    }


@cache.ttl_cache(ttl=(3600 * 24), is_skip_empty=True)
def get_fundamental_sell_rate(instrument_uid: str):
    final_rate = 0
    prediction = 0

    try:
        if (prediction := predictions_cache.get_prediction_cache(
                instrument_uid=instrument_uid,
                model_name=learn.model.TA_3_fundamental,
        )) and prediction < 0:
            rate = agent.utils.linear_interpolation(abs(prediction), 0, 0.05, 0, 1)
            final_rate = min(rate, 1)
    except Exception as e:
        logger.log_error(method_name='get_fundamental_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'prediction': prediction,
        },
    }
