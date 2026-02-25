import datetime
import os
import requests
from t_tech.invest import CandleInterval, HistoricCandle
from lib import docker, utils, logger, serializer

CANDLES_SERVICE_HOST = os.getenv('CANDLES_SERVICE_HOST', 'candles' if docker.is_docker() else 'localhost')
CANDLES_SERVICE_PORT = int(os.getenv('CANDLES_SERVICE_PORT', '8001'))
CANDLES_SERVICE_URL = f'http://{CANDLES_SERVICE_HOST}:{CANDLES_SERVICE_PORT}'


def get_interval_string(interval: CandleInterval) -> str:
    interval_map = {
        CandleInterval.CANDLE_INTERVAL_1_MIN: 'CANDLE_INTERVAL_1_MIN',
        CandleInterval.CANDLE_INTERVAL_5_MIN: 'CANDLE_INTERVAL_5_MIN',
        CandleInterval.CANDLE_INTERVAL_15_MIN: 'CANDLE_INTERVAL_15_MIN',
        CandleInterval.CANDLE_INTERVAL_HOUR: 'CANDLE_INTERVAL_HOUR',
        CandleInterval.CANDLE_INTERVAL_DAY: 'CANDLE_INTERVAL_DAY',
        CandleInterval.CANDLE_INTERVAL_WEEK: 'CANDLE_INTERVAL_WEEK',
        CandleInterval.CANDLE_INTERVAL_MONTH: 'CANDLE_INTERVAL_MONTH',
    }
    return interval_map.get(interval, 'CANDLE_INTERVAL_DAY')


def get_candles(
    ticker: str,
    date_from: datetime.datetime,
    date_to: datetime.datetime,
    interval: CandleInterval
) -> list[HistoricCandle]:
    try:
        response = requests.post(
            f'{CANDLES_SERVICE_URL}/candles',
            json={
                'instrument_ticker': ticker,
                'date_from': date_from.isoformat(),
                'date_to': date_to.isoformat(),
                'interval': get_interval_string(interval)
            },
            timeout=30
        )
        
        if response.status_code == 200:
            candles_data = response.json()
            
            result = []
            for candle in candles_data:
                historic_candle = HistoricCandle(
                    open=utils.get_quotation_by_price(candle['open_price']),
                    high=utils.get_quotation_by_price(candle['max_price']),
                    low=utils.get_quotation_by_price(candle['min_price']),
                    close=utils.get_quotation_by_price(candle['close_price']),
                    volume=int(candle['volume']),
                    time=datetime.datetime.fromisoformat(candle['date'].replace('Z', '+00:00')),
                    is_complete=True
                )
                result.append(historic_candle)
            
            return result
        else:
            logger.log_error(
                method_name='candles_client.get_candles response is not 200',
                debug_info=serializer.to_json(response),
                is_telegram_send=False,
            )
            return []
            
    except Exception as e:
        logger.log_error(method_name='candles_client.get_candles', error=e, is_telegram_send=False)
        return []
