import datetime
from lib import tech_analysis, agent, utils, logger, date_utils, cache
from t_tech.invest.schemas import IndicatorType, IndicatorInterval, TechAnalysisItem

RSI_CANDLES_COUNT = 7


@cache.ttl_cache(ttl=3600)
def rsi_buy_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    rsi_graph = _get_rsi_graph(instrument_uid=instrument_uid, date=date)
    rsi_value = rsi_graph[-1] if rsi_graph else None

    if rsi_value is not None:
        if rsi_value <= 30:
            final_rate = agent.utils.linear_interpolation(rsi_value, 0, 30, 1, 0.75)
        elif rsi_value <= 50:
                final_rate = agent.utils.linear_interpolation(rsi_value, 30, 50, 0.75, 0.001)

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'rsi_value': rsi_value,
            'graph': rsi_graph,
        },
    }


@cache.ttl_cache(ttl=3600)
def rsi_sell_rate(instrument_uid: str, date: datetime.datetime or None = None):
    final_rate = 0
    rsi_graph = _get_rsi_graph(instrument_uid=instrument_uid, date=date)
    rsi_value = rsi_graph[-1] if rsi_graph else None

    if rsi_value:
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
            'graph': rsi_graph,
        },
    }


def _get_rsi_graph(instrument_uid: str, date: datetime.datetime or None = None) -> list[float] or None:
    try:
        now = date or date_utils.get_day_prediction_time(date=datetime.datetime.now(tz=datetime.timezone.utc))
        graph = tech_analysis.get_tech_analysis(
            instrument_uid=instrument_uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_RSI,
            date_from=now - datetime.timedelta(days=(RSI_CANDLES_COUNT * 2)),
            date_to=now,
            interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
            length=14,
        )

        if graph and len(graph):
            graph_sorted = sorted(graph, key=lambda x: x.timestamp, reverse=False)[:RSI_CANDLES_COUNT]

            if len(graph_sorted) == RSI_CANDLES_COUNT:
                return [utils.get_price_by_quotation(i.signal) for i in graph_sorted]

    except Exception as e:
        logger.log_error(method_name='get_last_rsi_value', error=e, is_telegram_send=False)

    return None
