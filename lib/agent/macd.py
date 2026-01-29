import datetime
from lib import tech_analysis, utils
from tinkoff.invest.schemas import IndicatorType, IndicatorInterval

def macd_buy_rate(instrument_uid: str):
    final_rate = 0
    graph_hist = []
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    graph = tech_analysis.get_tech_analysis_graph(
        instrument_uid=instrument_uid,
        indicator_type=IndicatorType.INDICATOR_TYPE_MACD,
        date_from=now - datetime.timedelta(days=7),
        date_to=now,
        interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
    )

    if graph and len(graph):
        graph_sorted = sorted(graph, key=lambda x: x['date'], reverse=True)
        graph_hist = [utils.round_float((i.get('macd', 0) - i.get('signal', 0)), 3) for i in graph_sorted]

        if all(i < 0 for i in graph_hist):
            final_rate = 50

            if graph_hist[0] > graph_hist[1]:
                final_rate = 60

                if graph_hist[1] == min(graph_hist):
                    final_rate = 100
                elif graph_hist[2] == min(graph_hist) and graph_hist[1] > graph_hist[2]:
                    final_rate = 70

    return {'rate': final_rate, 'graph_hist': graph_hist}


def macd_sell_rate(instrument_uid: str):
    final_rate = 0
    graph_hist = []
    now = datetime.datetime.now(tz=datetime.timezone.utc)
    graph = tech_analysis.get_tech_analysis_graph(
        instrument_uid=instrument_uid,
        indicator_type=IndicatorType.INDICATOR_TYPE_MACD,
        date_from=now - datetime.timedelta(days=7),
        date_to=now,
        interval=IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
    )

    if graph and len(graph):
        graph_sorted = sorted(graph, key=lambda x: x['date'], reverse=True)
        graph_hist = [utils.round_float((i.get('macd', 0) - i.get('signal', 0)), 3) for i in graph_sorted]

        if all(i > 0 for i in graph_hist):
            final_rate = 50

            if graph_hist[0] < graph_hist[1]:
                final_rate = 60

                if graph_hist[1] == max(graph_hist):
                    final_rate = 100
                elif graph_hist[2] == max(graph_hist) and graph_hist[1] < graph_hist[2]:
                    final_rate = 70

    return {'rate': final_rate, 'graph_hist': graph_hist}