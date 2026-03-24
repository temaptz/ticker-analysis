import datetime
from lib import tech_analysis, utils, cache, logger
from t_tech.invest.schemas import IndicatorType, IndicatorInterval

MACD_CANDLES_COUNT = 7


@cache.ttl_cache(ttl=3600)
def macd_buy_rate(instrument_uid: str, date: datetime.datetime or None = None) -> dict:
    final_rate = 0
    graph = _get_last_macd_hist(instrument_uid=instrument_uid, date=date)
    graph_hist = graph[::-1] if graph else None

    if graph_hist:
        if all(i < 0 for i in graph_hist):
            final_rate = 0.5

            if graph_hist[0] > graph_hist[1]:
                final_rate = 0.6

                if graph_hist[1] == min(graph_hist):
                    final_rate = 1
                elif graph_hist[2] == min(graph_hist) and graph_hist[1] > graph_hist[2]:
                    final_rate = 0.7

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'graph': graph,
        },
    }


@cache.ttl_cache(ttl=3600)
def macd_sell_rate(instrument_uid: str, date: datetime.datetime or None = None) -> dict:
    final_rate = 0
    graph = _get_last_macd_hist(instrument_uid=instrument_uid, date=date)
    graph_hist = graph[::-1] if graph else None

    if graph_hist:
        if all(i > 0 for i in graph_hist):
            final_rate = 0.5

            if graph_hist[0] < graph_hist[1]:
                final_rate = 0.6

                if graph_hist[1] == max(graph_hist):
                    final_rate = 1
                elif graph_hist[2] == max(graph_hist) and graph_hist[1] < graph_hist[2]:
                    final_rate = 0.7

    return {
        'rate': final_rate,
        'debug': {
            'rate': final_rate,
            'graph': graph,
        },
    }

def _get_last_macd_hist(instrument_uid: str, date: datetime.datetime or None = None) -> list[float] or None:
    try:
        now = date or datetime.datetime.now(tz=datetime.timezone.utc)
        graph = tech_analysis.get_tech_analysis_graph(
            instrument_uid=instrument_uid,
            indicator_type=IndicatorType.INDICATOR_TYPE_MACD,
            date_from=now - datetime.timedelta(days=20),
            date_to=now,
            interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
        )

        if graph and len(graph):
            graph_sorted = sorted(graph, key=lambda x: x['date'], reverse=False)[:MACD_CANDLES_COUNT]
            graph_hist = [utils.round_float((i.get('macd', 0) - i.get('signal', 0)), 3) for i in graph_sorted]

            if len(graph_hist) == MACD_CANDLES_COUNT:
                return graph_hist

    except Exception as e:
        logger.log_error(method_name='get_last_macd_hist', error=e, is_telegram_send=False)

    return None