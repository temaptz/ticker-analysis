import datetime
from lib import tech_analysis, agent, utils, logger, date_utils
from t_tech.invest.schemas import IndicatorType, IndicatorInterval, TechAnalysisItem

RSI_CANDLES_COUNT = 7

def rsi_buy_rate(instrument_uid: str):
    final_rate = 0
    rsi_value = None
    rsi_date = None
    rsi_candle = get_last_rsi_candle(instrument_uid=instrument_uid)

    if rsi_candle:
        rsi_value = utils.get_price_by_quotation(rsi_candle.signal)
        rsi_date = rsi_candle.timestamp

        if rsi_value <= 30:
            final_rate = agent.utils.linear_interpolation(rsi_value, 0, 30, 1, 0.75)
        elif rsi_value <= 50:
                final_rate = agent.utils.linear_interpolation(rsi_value, 30, 50, 0.75, 0.001)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'rsi_value': rsi_value,
            'rsi_date': rsi_date,
        },
    }


def rsi_sell_rate(instrument_uid: str):
    final_rate = 0
    rsi_value = None
    rsi_date = None
    rsi_candle = get_last_rsi_candle(instrument_uid=instrument_uid)

    if rsi_candle:
        rsi_value = utils.get_price_by_quotation(rsi_candle.signal)
        rsi_date = rsi_candle.timestamp

        if rsi_value > 50:
            final_rate = agent.utils.linear_interpolation(rsi_value, 50, 100, 0.001, 1)

        if rsi_value >= 70:
            final_rate = agent.utils.linear_interpolation(rsi_value, 70, 100, 0.75, 1)
        elif rsi_value >= 50:
            final_rate = agent.utils.linear_interpolation(rsi_value, 50, 70, 0.001, 0.75)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'rsi_value': rsi_value,
            'rsi_date': rsi_date,
        },
    }


def get_last_rsi_candle(instrument_uid: str) -> TechAnalysisItem or None:
    try:
        now = date_utils.get_day_prediction_time(date=datetime.datetime.now(tz=datetime.timezone.utc))
        graph = tech_analysis.get_tech_analysis(
            instrument_uid=instrument_uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=now - datetime.timedelta(days=(RSI_CANDLES_COUNT * 2)),
            date_to=now,
            interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
            length=14,
        )

        if graph and len(graph):
            graph_sorted = sorted(graph, key=lambda x: x.timestamp, reverse=True)[:RSI_CANDLES_COUNT]

            if graph_sorted[0]:
                return graph_sorted[0]

    except Exception as e:
        logger.log_error(method_name='get_last_rsi_value', error=e, is_telegram_send=False)

    return None
