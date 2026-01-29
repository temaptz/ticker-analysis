import datetime
from tinkoff.invest import Client, CandleInterval, constants, InstrumentIdType, InstrumentResponse, HistoricCandle, LastPrice
import datetime

from tinkoff.invest.schemas import TechAnalysisItem, IndicatorType, GetTechAnalysisRequest, TypeOfPrice, \
    IndicatorInterval, Deviation, Smoothing

from const import TINKOFF_INVEST_TOKEN, TICKER_LIST
from lib import cache, utils, date_utils, logger


@cache.ttl_cache(ttl=3600 * 24)
def get_tech_analysis(
        instrument_uid: str,
        indicator_type: IndicatorType,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval: IndicatorInterval,
        length: int = 3,
        deviation: Deviation = None,
        smoothing: Smoothing = None,
) -> [TechAnalysisItem]:
    if indicator_type == IndicatorType.INDICATOR_TYPE_MACD and smoothing is None:
        smoothing = Smoothing(
            fast_length=12,
            slow_length=26,
            signal_smoothing=9,
        )
    with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
        return client.market_data.get_tech_analysis(
            request=GetTechAnalysisRequest(
                indicator_type=indicator_type,
                instrument_uid=instrument_uid,
                from_=date_from,
                to=date_to,
                interval=interval,
                type_of_price=TypeOfPrice.TYPE_OF_PRICE_AVG,
                length=length,
                deviation=deviation,
                smoothing=smoothing,
            )
        ).technical_indicators


# @DEPRECATED use get_tech_analysis_graph
@cache.ttl_cache(ttl=3600 * 24)
def get_avg_tech_analysis_by_date(
        instrument_uid: str,
        indicator_type: IndicatorType,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval: IndicatorInterval = IndicatorInterval.INDICATOR_INTERVAL_ONE_DAY,
        length: int = 3,
        deviation: Deviation = None,
        smoothing: Smoothing = None,
) -> float or None:
    signals = []

    for i in get_tech_analysis(
            instrument_uid=instrument_uid,
            indicator_type=indicator_type,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
            deviation=deviation,
            smoothing=smoothing,
            length=length,
    ) or []:
        if i.signal:
            signal = utils.get_price_by_quotation(i.signal)
            if signal or signal == 0:
                signals.append(signal)

    return sum(signals) / len(signals) if len(signals) else None


def get_tech_analysis_graph(
        instrument_uid: str,
        indicator_type: IndicatorType,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        interval: IndicatorInterval,
        length: int = 3,
        deviation: Deviation = None,
        smoothing: Smoothing = None,
) -> list:
    result = []

    for i in get_tech_analysis(
            instrument_uid=instrument_uid,
            indicator_type=indicator_type,
            date_from=date_from,
            date_to=date_to,
            interval=interval,
            deviation=deviation,
            smoothing=smoothing,
            length=length,
    ) or []:
        result.append({
            'signal': utils.get_price_by_quotation(i.signal) if i.signal else None,
            'middle_band': utils.get_price_by_quotation(i.middle_band) if i.middle_band else None,
            'macd': utils.get_price_by_quotation(i.macd) if i.macd else None,
            'date': date_utils.parse_date(i.timestamp),
        })

    return result
