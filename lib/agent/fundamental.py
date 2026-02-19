from lib import logger, db_2


def get_fundamental_buy_rate(instrument_uid: str):
    final_rate = 0

    try:
        llm_tag = db_2.instrument_tags_db.get_tag(instrument_uid=instrument_uid, tag_name='llm_fundamental_rate')
        if llm_tag and (llm_tag.tag_value or llm_tag.tag_value == 0):
            final_rate = float(llm_tag.tag_value) / 100

    except Exception as e:
        logger.log_error(method_name='get_fundamental_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
        },
    }


def get_fundamental_sell_rate(instrument_uid: str):
    final_rate = 0

    try:
        final_rate = 0
    except Exception as e:
        logger.log_error(method_name='get_fundamental_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
        },
    }
