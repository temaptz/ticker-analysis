import datetime
from lib import tech_analysis, agent, utils, logger
from t_tech.invest.schemas import IndicatorType, IndicatorInterval

RSI_CANDLES_COUNT = 7

def rsi_buy_rate(instrument_uid: str):
    final_rate = 0
    rsi_value = None

    try:

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        graph = tech_analysis.get_tech_analysis(
            instrument_uid=instrument_uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=now - datetime.timedelta(days=20),
            date_to=now,
            interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
        )

        if graph and len(graph):
            graph_sorted = sorted(graph, key=lambda x: x['date'], reverse=True)[:RSI_CANDLES_COUNT]
            if graph_sorted[0].signal:
                rsi_value = utils.get_price_by_quotation(graph_sorted[0].signal)

                if rsi_value and rsi_value < 50:
                    final_rate = agent.utils.linear_interpolation(rsi_value, 0, 50, 100, 50)
    except Exception as e:
        logger.log_error(method_name='rsi_buy_rate', error=e, is_telegram_send=False)

    return {'rate': final_rate, 'rsi_value': rsi_value}


def rsi_sell_rate(instrument_uid: str):
    final_rate = 0
    rsi_value = None

    try:

        now = datetime.datetime.now(tz=datetime.timezone.utc)
        graph = tech_analysis.get_tech_analysis(
            instrument_uid=instrument_uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=now - datetime.timedelta(days=20),
            date_to=now,
            interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
        )

        if graph and len(graph):
            graph_sorted = sorted(graph, key=lambda x: x['date'], reverse=True)[:RSI_CANDLES_COUNT]
            if graph_sorted[0].signal:
                rsi_value = utils.get_price_by_quotation(graph_sorted[0].signal)

                if rsi_value and rsi_value > 50:
                    final_rate = agent.utils.linear_interpolation(rsi_value, 50, 100, 50, 100)
    except Exception as e:
        logger.log_error(method_name='rsi_sell_rate', error=e, is_telegram_send=False)

    return {'rate': final_rate, 'rsi_value': rsi_value}