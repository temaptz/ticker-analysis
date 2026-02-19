from lib import logger


def get_volume_buy_rate(instrument_uid: str):
    final_rate = 0

    try:
        final_rate = 0
    except Exception as e:
        logger.log_error(method_name='get_volume_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
        },
    }


def get_volume_sell_rate(instrument_uid: str):
    final_rate = 0

    try:
        final_rate = 0
    except Exception as e:
        logger.log_error(method_name='get_volume_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
        },
    }
