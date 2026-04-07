import datetime
from lib import logger, cache, learn


def get_consensus_buy_rate(instrument_uid: str, account_id: str, date: datetime.datetime or None = None):
    final_rate = 0

    try:
        if prediction := _get_prediction(instrument_uid=instrument_uid, account_id=account_id, is_buy=True, date=date):
            final_rate = prediction
    except Exception as e:
        logger.log_error(method_name='get_consensus_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
        },
    }


def get_consensus_sell_rate(instrument_uid: str, account_id: str, date: datetime.datetime or None = None):
    final_rate = 0

    try:
        if prediction := _get_prediction(instrument_uid=instrument_uid, account_id=account_id, is_buy=False, date=date):
            final_rate = prediction
    except Exception as e:
        logger.log_error(method_name='get_consensus_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
        },
    }


@cache.ttl_cache(ttl=3600)
def _get_prediction(instrument_uid: str, account_id: str, is_buy: bool, date: datetime.datetime or None = None) -> float or None:
    return learn.ta_consensus_learn.predict_future(
        instrument_uid=instrument_uid,
        account_id=account_id,
        is_buy=is_buy,
        date_current=date,
        is_fill_empty=True,
    )
