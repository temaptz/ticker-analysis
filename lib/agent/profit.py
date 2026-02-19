from lib import logger, invest_calc, users, agent, utils, serializer


def get_profit_buy_rate(instrument_uid: str):
    final_rate = 0

    try:
        final_rate = 0
    except Exception as e:
        logger.log_error(method_name='get_profit_buy_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'potential_profit_percent': None,
        },
    }


def get_profit_sell_rate(instrument_uid: str):
    final_rate = 0
    potential_profit_percent = None

    try:
        if calc := invest_calc.get_invest_calc_by_instrument_uid(
                instrument_uid=instrument_uid,
                account_id=users.get_analytics_account().id,
        ):
            if (p := calc['potential_profit_percent']) or p == 0:
                if p <= 0:
                    rate = 0
                elif 0 < p <= 3:
                    rate = agent.utils.lerp(p, 0, 3, 0, 0.5)
                else:
                    rate = min(1.00, agent.utils.lerp(p, 3, 15, 0.5, 1))


                if rate or rate == 0:
                    final_rate = rate
                potential_profit_percent = p
    except Exception as e:
        logger.log_error(method_name='get_profit_sell_rate', error=e, is_telegram_send=False)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'potential_profit_percent': potential_profit_percent,
        },
    }
