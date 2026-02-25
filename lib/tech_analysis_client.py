"""
Client for calling tech analysis from candles service
"""
import datetime
import os
import requests
from typing import Optional, List
from t_tech.invest.schemas import TechAnalysisItem, Quotation

from lib import logger, utils

CANDLES_SERVICE_HOST = os.getenv('CANDLES_SERVICE_HOST', 'candles')
CANDLES_SERVICE_PORT = os.getenv('CANDLES_SERVICE_PORT', '8001')
CANDLES_SERVICE_URL = f'http://{CANDLES_SERVICE_HOST}:{CANDLES_SERVICE_PORT}'


@logger.error_logger
def get_tech_analysis_from_service(
    instrument_ticker: str,
    indicator_type: int,
    date_from: datetime.datetime,
    date_to: datetime.datetime,
    interval: int,
    length: Optional[int] = None,
    deviation_multiplier: Optional[float] = None,
    fast_length: Optional[int] = None,
    slow_length: Optional[int] = None,
    signal_smoothing: Optional[int] = None
) -> List[TechAnalysisItem]:
    """
    Get technical analysis from candles service
    
    Args:
        instrument_ticker: Ticker of the instrument
        indicator_type: Type of indicator (1=BB, 2=EMA, 3=RSI, 4=MACD, 6=OBV, 7=SMA)
        date_from: Start date
        date_to: End date
        interval: Candle interval (1=1min, 2=5min, 3=15min, 4=1hour, 5=1day, etc.)
        length: Period length for indicators
        deviation_multiplier: Standard deviation multiplier for Bollinger Bands
        fast_length: Fast EMA length for MACD
        slow_length: Slow EMA length for MACD
        signal_smoothing: Signal line smoothing for MACD
    
    Returns:
        List of TechAnalysisItem objects
    """
    url = f'{CANDLES_SERVICE_URL}/tech_analysis'
    
    params = {
        'instrument_ticker': instrument_ticker,
        'indicator_type': indicator_type,
        'date_from': date_from.isoformat(),
        'date_to': date_to.isoformat(),
        'interval': interval
    }
    
    if length is not None:
        params['length'] = length
    if deviation_multiplier is not None:
        params['deviation_multiplier'] = deviation_multiplier
    if fast_length is not None:
        params['fast_length'] = fast_length
    if slow_length is not None:
        params['slow_length'] = slow_length
    if signal_smoothing is not None:
        params['signal_smoothing'] = signal_smoothing
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    result = []
    for item in data:
        timestamp = datetime.datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
        
        tech_item = TechAnalysisItem(
            timestamp=timestamp,
            signal=utils.get_quotation_by_price(item['signal']) if item['signal'] is not None else None,
            middle_band=utils.get_quotation_by_price(item['middle_band']) if item['middle_band'] is not None else None,
            macd=utils.get_quotation_by_price(item['macd']) if item['macd'] is not None else None
        )
        result.append(tech_item)
    
    return result
