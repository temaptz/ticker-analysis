import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from t_tech.invest import Client, CandleInterval, constants
from const import TINKOFF_INVEST_TOKEN
from lib import logger, redis_utils, utils, date_utils
from lib.db_2 import candles_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.log_info(message='Before candles service started')
    candles_db.init_table()
    logger.log_info(message='Candles service started')
    yield
    logger.log_info(message='Candles service shutting down')


app = FastAPI(lifespan=lifespan)


class CandleRequest(BaseModel):
    instrument_ticker: str
    date_from: datetime.datetime
    date_to: datetime.datetime
    interval: str


class CandleResponse(BaseModel):
    ticker: str
    date: datetime.datetime
    open_price: float
    close_price: float
    min_price: float
    max_price: float
    volume: float


def get_candle_interval_from_string(interval_str: str) -> CandleInterval:
    interval_map = {
        'CANDLE_INTERVAL_1_MIN': CandleInterval.CANDLE_INTERVAL_1_MIN,
        'CANDLE_INTERVAL_5_MIN': CandleInterval.CANDLE_INTERVAL_5_MIN,
        'CANDLE_INTERVAL_15_MIN': CandleInterval.CANDLE_INTERVAL_15_MIN,
        'CANDLE_INTERVAL_HOUR': CandleInterval.CANDLE_INTERVAL_HOUR,
        'CANDLE_INTERVAL_DAY': CandleInterval.CANDLE_INTERVAL_DAY,
        'CANDLE_INTERVAL_WEEK': CandleInterval.CANDLE_INTERVAL_WEEK,
        'CANDLE_INTERVAL_MONTH': CandleInterval.CANDLE_INTERVAL_MONTH,
    }
    return interval_map.get(interval_str, CandleInterval.CANDLE_INTERVAL_DAY)


def get_interval_seconds(interval: CandleInterval) -> int:
    interval_seconds = {
        CandleInterval.CANDLE_INTERVAL_1_MIN: 60,
        CandleInterval.CANDLE_INTERVAL_5_MIN: 300,
        CandleInterval.CANDLE_INTERVAL_15_MIN: 900,
        CandleInterval.CANDLE_INTERVAL_HOUR: 3600,
        CandleInterval.CANDLE_INTERVAL_DAY: 86400,
        CandleInterval.CANDLE_INTERVAL_WEEK: 604800,
        CandleInterval.CANDLE_INTERVAL_MONTH: 2592000,
    }
    return interval_seconds.get(interval, 86400)


def fetch_candles_from_tinkoff(ticker: str, date_from: datetime.datetime, date_to: datetime.datetime) -> list[dict]:
    try:
        with Client(token=TINKOFF_INVEST_TOKEN, target=constants.INVEST_GRPC_API) as client:
            from lib import instruments
            instrument = instruments.get_instrument_by_ticker(ticker=ticker)
            
            if not instrument:
                logger.log_error(method_name='fetch_candles_from_tinkoff', error=f'Instrument not found: {ticker}')
                return []
            
            date_from_utc = date_from if date_from.tzinfo else date_from.replace(tzinfo=datetime.timezone.utc)
            date_to_utc = date_to if date_to.tzinfo else date_to.replace(tzinfo=datetime.timezone.utc)
            
            candles = client.market_data.get_candles(
                instrument_id=instrument.uid,
                from_=date_from_utc,
                to=date_to_utc,
                interval=CandleInterval.CANDLE_INTERVAL_DAY
            ).candles
            
            result = []
            for candle in candles:
                candle_time_utc = date_utils.convert_to_utc(candle.time) if candle.time.tzinfo else candle.time.replace(tzinfo=datetime.timezone.utc)
                result.append({
                    'ticker': ticker,
                    'date': candle_time_utc.replace(tzinfo=None),
                    'open_price': utils.get_price_by_quotation(candle.open),
                    'close_price': utils.get_price_by_quotation(candle.close),
                    'min_price': utils.get_price_by_quotation(candle.low),
                    'max_price': utils.get_price_by_quotation(candle.high),
                    'volume': float(candle.volume),
                    'is_complete': candle.is_complete
                })
            
            return result
    except Exception as e:
        logger.log_error(method_name='fetch_candles_from_tinkoff', error=e)
        return []


def aggregate_candles(candles: list[dict], interval: CandleInterval) -> list[dict]:
    if interval == CandleInterval.CANDLE_INTERVAL_DAY:
        return candles
    
    interval_seconds = get_interval_seconds(interval)
    
    if not candles:
        return []
    
    aggregated = []
    current_group = []
    group_start_time = None
    
    for candle in sorted(candles, key=lambda x: x['date']):
        candle_time = candle['date']
        
        if group_start_time is None:
            group_start_time = candle_time
            current_group = [candle]
        else:
            time_diff = (candle_time - group_start_time).total_seconds()
            
            if time_diff < interval_seconds:
                current_group.append(candle)
            else:
                if current_group:
                    aggregated.append(merge_candles(current_group))
                
                group_start_time = candle_time
                current_group = [candle]
    
    if current_group:
        aggregated.append(merge_candles(current_group))
    
    return aggregated


def merge_candles(candles: list[dict]) -> dict:
    if not candles:
        return None
    
    if len(candles) == 1:
        return candles[0]
    
    sorted_candles = sorted(candles, key=lambda x: x['date'])
    
    return {
        'ticker': sorted_candles[0]['ticker'],
        'date': sorted_candles[0]['date'],
        'open_price': sorted_candles[0]['open_price'],
        'close_price': sorted_candles[-1]['close_price'],
        'min_price': min(c['min_price'] for c in sorted_candles),
        'max_price': max(c['max_price'] for c in sorted_candles),
        'volume': sum(c['volume'] for c in sorted_candles)
    }


def get_incomplete_candle_from_cache(ticker: str, date: datetime.datetime) -> Optional[dict]:
    cache_key = f'incomplete_candle:{ticker}:{date.isoformat()}'
    return redis_utils.cache_get(key=cache_key)


def save_incomplete_candle_to_cache(candle: dict, ttl: int = 3600) -> None:
    cache_key = f'incomplete_candle:{candle["ticker"]}:{candle["date"].isoformat()}'
    redis_utils.cache_set(key=cache_key, value=candle, ttl_sec=ttl)


@app.post("/candles", response_model=list[CandleResponse])
async def get_candles(request: CandleRequest):
    try:
        ticker = request.instrument_ticker
        date_from = request.date_from
        date_to = request.date_to
        interval = get_candle_interval_from_string(request.interval)
        
        if date_from.tzinfo is None:
            date_from = date_from.replace(tzinfo=datetime.timezone.utc)
        else:
            date_from = date_from.astimezone(datetime.timezone.utc)
            
        if date_to.tzinfo is None:
            date_to = date_to.replace(tzinfo=datetime.timezone.utc)
        else:
            date_to = date_to.astimezone(datetime.timezone.utc)
        
        date_from_utc = date_from
        date_to_utc = date_to
        
        db_candles = candles_db.get_candles(
            ticker=ticker,
            date_from=date_from_utc,
            date_to=date_to_utc
        )
        
        db_candles_dict = [
            {
                'ticker': c.ticker,
                'date': c.date,
                'open_price': c.open_price,
                'close_price': c.close_price,
                'min_price': c.min_price,
                'max_price': c.max_price,
                'volume': c.volume
            }
            for c in db_candles
        ]
        
        missing_ranges = candles_db.get_missing_date_ranges(
            ticker=ticker,
            date_from=date_from_utc,
            date_to=date_to_utc
        )
        
        fetched_candles = []
        for range_from, range_to in missing_ranges:
            new_candles = fetch_candles_from_tinkoff(
                ticker=ticker,
                date_from=range_from,
                date_to=range_to
            )
            
            complete_candles = [c for c in new_candles if c.get('is_complete', True)]
            incomplete_candles = [c for c in new_candles if not c.get('is_complete', True)]
            
            if complete_candles:
                candles_db.bulk_insert_candles(complete_candles)
                fetched_candles.extend(complete_candles)
            
            for inc_candle in incomplete_candles:
                save_incomplete_candle_to_cache(inc_candle)
                fetched_candles.append(inc_candle)
        
        all_candles = db_candles_dict + fetched_candles
        
        today = datetime.datetime.now(datetime.timezone.utc).date()
        for candle in all_candles:
            if candle['date'].date() == today:
                cached = get_incomplete_candle_from_cache(ticker, candle['date'])
                if cached:
                    candle.update(cached)
        
        all_candles = sorted(all_candles, key=lambda x: x['date'])
        
        if interval != CandleInterval.CANDLE_INTERVAL_DAY:
            all_candles = aggregate_candles(all_candles, interval)
        
        response = [
            CandleResponse(
                ticker=c['ticker'],
                date=c['date'],
                open_price=c['open_price'],
                close_price=c['close_price'],
                min_price=c['min_price'],
                max_price=c['max_price'],
                volume=c['volume']
            )
            for c in all_candles
        ]
        
        return response
        
    except Exception as e:
        logger.log_error(method_name='get_candles', error=e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
