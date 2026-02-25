"""
Technical Analysis module for candles service
Calculates technical indicators using pandas and pandas-ta library
"""
import pandas as pd
from typing import Optional, List, Dict, Any

from lib import logger


class TechnicalAnalysis:
    """Technical analysis calculator using pandas"""
    
    def __init__(self, candles: List[Dict[str, Any]]):
        """
        Initialize with candle data
        
        Args:
            candles: List of candle dicts with keys: date, open_price, close_price, min_price, max_price, volume
        """
        if not candles:
            self.df = pd.DataFrame()
            return
        
        self.df = pd.DataFrame(candles)
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df = self.df.sort_values('date')
        self.df = self.df.rename(columns={
            'open_price': 'open',
            'close_price': 'close',
            'min_price': 'low',
            'max_price': 'high',
            'volume': 'volume'
        })
        self.df = self.df.set_index('date')
    
    def calculate_sma(self, length: int = 20) -> pd.Series:
        """Simple Moving Average"""
        return self.df['close'].rolling(window=length).mean()
    
    def calculate_ema(self, length: int = 20) -> pd.Series:
        """Exponential Moving Average"""
        return self.df['close'].ewm(span=length, adjust=False).mean()
    
    def calculate_rsi(self, length: int = 14) -> pd.Series:
        """
        Relative Strength Index
        
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        """
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=length).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=length).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, fast_length: int = 12, slow_length: int = 26, signal_smoothing: int = 9) -> Dict[str, pd.Series]:
        """
        Moving Average Convergence Divergence
        
        Returns:
            dict with 'macd', 'signal', 'histogram'
        """
        ema_fast = self.df['close'].ewm(span=fast_length, adjust=False).mean()
        ema_slow = self.df['close'].ewm(span=slow_length, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_smoothing, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def calculate_bollinger_bands(self, length: int = 20, std_dev: float = 2.0) -> Dict[str, pd.Series]:
        """
        Bollinger Bands
        
        Returns:
            dict with 'upper', 'middle', 'lower'
        """
        middle = self.df['close'].rolling(window=length).mean()
        std = self.df['close'].rolling(window=length).std()
        
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    def calculate_obv(self) -> pd.Series:
        """On-Balance Volume"""
        obv = pd.Series(index=self.df.index, dtype=float)
        obv.iloc[0] = self.df['volume'].iloc[0]
        
        for i in range(1, len(self.df)):
            if self.df['close'].iloc[i] > self.df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + self.df['volume'].iloc[i]
            elif self.df['close'].iloc[i] < self.df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - self.df['volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv


@logger.error_logger
def calculate_indicator(
    candles: List[Dict[str, Any]],
    indicator_type: str,
    length: Optional[int] = None,
    deviation_multiplier: Optional[float] = None,
    fast_length: Optional[int] = None,
    slow_length: Optional[int] = None,
    signal_smoothing: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Calculate technical indicator for given candles
    
    Args:
        candles: List of candle dicts
        indicator_type: Type of indicator (SMA, EMA, RSI, MACD, BB, OBV)
        length: Period length for most indicators
        deviation_multiplier: Standard deviation multiplier for Bollinger Bands
        fast_length: Fast EMA length for MACD
        slow_length: Slow EMA length for MACD
        signal_smoothing: Signal line smoothing for MACD
    
    Returns:
        List of dicts with timestamp and indicator values
    """
    if not candles:
        return []
    
    ta = TechnicalAnalysis(candles)
    
    if ta.df.empty:
        return []
    
    result = []
    
    if indicator_type == 'SMA':
        length = length or 20
        sma = ta.calculate_sma(length)
        for timestamp, value in sma.items():
            if pd.notna(value):
                result.append({
                    'timestamp': timestamp,
                    'signal': float(value),
                    'middle_band': None,
                    'macd': None
                })
    
    elif indicator_type == 'EMA':
        length = length or 20
        ema = ta.calculate_ema(length)
        for timestamp, value in ema.items():
            if pd.notna(value):
                result.append({
                    'timestamp': timestamp,
                    'signal': float(value),
                    'middle_band': None,
                    'macd': None
                })
    
    elif indicator_type == 'RSI':
        length = length or 14
        rsi = ta.calculate_rsi(length)
        for timestamp, value in rsi.items():
            if pd.notna(value):
                result.append({
                    'timestamp': timestamp,
                    'signal': float(value),
                    'middle_band': None,
                    'macd': None
                })
    
    elif indicator_type == 'MACD':
        fast_length = fast_length or 12
        slow_length = slow_length or 26
        signal_smoothing = signal_smoothing or 9
        
        macd_data = ta.calculate_macd(fast_length, slow_length, signal_smoothing)
        
        for timestamp in macd_data['macd'].index:
            macd_val = macd_data['macd'].loc[timestamp]
            signal_val = macd_data['signal'].loc[timestamp]
            
            if pd.notna(macd_val) and pd.notna(signal_val):
                result.append({
                    'timestamp': timestamp,
                    'signal': float(signal_val),
                    'middle_band': None,
                    'macd': float(macd_val)
                })
    
    elif indicator_type == 'BB':
        length = length or 20
        deviation_multiplier = deviation_multiplier or 2.0
        
        bb = ta.calculate_bollinger_bands(length, deviation_multiplier)
        
        for timestamp in bb['middle'].index:
            upper_val = bb['upper'].loc[timestamp]
            middle_val = bb['middle'].loc[timestamp]
            lower_val = bb['lower'].loc[timestamp]
            
            if pd.notna(middle_val):
                result.append({
                    'timestamp': timestamp,
                    'signal': float(lower_val) if pd.notna(lower_val) else None,
                    'middle_band': float(middle_val),
                    'macd': float(upper_val) if pd.notna(upper_val) else None
                })
    
    elif indicator_type == 'OBV':
        obv = ta.calculate_obv()
        for timestamp, value in obv.items():
            if pd.notna(value):
                result.append({
                    'timestamp': timestamp,
                    'signal': float(value),
                    'middle_band': None,
                    'macd': None
                })
    
    return result


def map_tinkoff_indicator_type(indicator_type_int: int) -> str:
    """
    Map Tinkoff IndicatorType enum to string
    
    INDICATOR_TYPE_BB = 1
    INDICATOR_TYPE_EMA = 2
    INDICATOR_TYPE_RSI = 3
    INDICATOR_TYPE_MACD = 4
    INDICATOR_TYPE_PRICE_CHANNEL = 5
    INDICATOR_TYPE_OBV = 6
    INDICATOR_TYPE_SMA = 7
    """
    mapping = {
        1: 'BB',
        2: 'EMA',
        3: 'RSI',
        4: 'MACD',
        5: 'PRICE_CHANNEL',
        6: 'OBV',
        7: 'SMA'
    }
    return mapping.get(indicator_type_int, 'UNKNOWN')


def map_tinkoff_interval(interval_int: int) -> str:
    """
    Map Tinkoff IndicatorInterval enum to CandleInterval string
    
    INDICATOR_INTERVAL_ONE_MINUTE = 1
    INDICATOR_INTERVAL_FIVE_MINUTES = 2
    INDICATOR_INTERVAL_FIFTEEN_MINUTES = 3
    INDICATOR_INTERVAL_ONE_HOUR = 4
    INDICATOR_INTERVAL_ONE_DAY = 5
    INDICATOR_INTERVAL_2_MIN = 6
    INDICATOR_INTERVAL_3_MIN = 7
    INDICATOR_INTERVAL_10_MIN = 8
    INDICATOR_INTERVAL_30_MIN = 9
    INDICATOR_INTERVAL_2_HOUR = 10
    INDICATOR_INTERVAL_4_HOUR = 11
    INDICATOR_INTERVAL_WEEK = 12
    INDICATOR_INTERVAL_MONTH = 13
    """
    mapping = {
        1: 'CANDLE_INTERVAL_1_MIN',
        2: 'CANDLE_INTERVAL_5_MIN',
        3: 'CANDLE_INTERVAL_15_MIN',
        4: 'CANDLE_INTERVAL_HOUR',
        5: 'CANDLE_INTERVAL_DAY',
        6: 'CANDLE_INTERVAL_2_MIN',
        7: 'CANDLE_INTERVAL_3_MIN',
        8: 'CANDLE_INTERVAL_10_MIN',
        9: 'CANDLE_INTERVAL_30_MIN',
        10: 'CANDLE_INTERVAL_2_HOUR',
        11: 'CANDLE_INTERVAL_4_HOUR',
        12: 'CANDLE_INTERVAL_WEEK',
        13: 'CANDLE_INTERVAL_MONTH'
    }
    return mapping.get(interval_int, 'CANDLE_INTERVAL_DAY')
