import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, Float, String, Boolean, BigInteger, Index, and_
from sqlalchemy.orm import declarative_base, Session
from lib.db_2.connection import get_engine
from lib import logger

Base = declarative_base()
engine = get_engine()


class CandleDB(Base):
    __tablename__ = 'candles'

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String, nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    min_price = Column(Float, nullable=False)
    max_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    is_complete = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    __table_args__ = (
        Index('idx_ticker_date', 'ticker', 'date'),
        Index('idx_ticker_date_complete', 'ticker', 'date', 'is_complete'),
    )


@logger.error_logger
def drop_table() -> None:
    Base.metadata.drop_all(engine, tables=[CandleDB.__table__])


@logger.error_logger
def init_table() -> None:
    from sqlalchemy import inspect, text
    
    inspector = inspect(engine)
    
    if 'candles' in inspector.get_table_names():
        columns = inspector.get_columns('candles')
        id_column = next((col for col in columns if col['name'] == 'id'), None)
        
        if id_column and str(id_column['type']) == 'UUID':
            print('Candles table exists with old UUID schema, dropping and recreating with BigInteger...')
            drop_table()
            Base.metadata.create_all(engine, checkfirst=False)
        else:
            Base.metadata.create_all(engine, checkfirst=True)
            
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = 'idx_ticker_date_complete'
                """))
                
                if not result.fetchone():
                    print('Creating composite index idx_ticker_date_complete...')
                    conn.execute(text("""
                        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ticker_date_complete 
                        ON candles (ticker, date, is_complete)
                    """))
                    conn.commit()
                    print('Composite index created successfully')
    else:
        Base.metadata.create_all(engine, checkfirst=True)


@logger.error_logger
def get_candles(
    ticker: str,
    date_from: datetime.datetime,
    date_to: datetime.datetime
) -> list[CandleDB]:
    with Session(engine) as session:
        if date_from.tzinfo is not None:
            date_from = date_from.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if date_to.tzinfo is not None:
            date_to = date_to.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        
        query = session.query(CandleDB).filter(
            and_(
                CandleDB.ticker == ticker,
                CandleDB.date >= date_from,
                CandleDB.date <= date_to,
                CandleDB.is_complete == True
            )
        ).order_by(CandleDB.date)
        
        return query.all()


@logger.error_logger
def insert_candle(
    ticker: str,
    date: datetime.datetime,
    open_price: float,
    close_price: float,
    min_price: float,
    max_price: float,
    volume: float,
    is_complete: bool = True
) -> None:
    with Session(engine) as session:
        existing = session.query(CandleDB).filter(
            and_(
                CandleDB.ticker == ticker,
                CandleDB.date == date
            )
        ).first()
        
        if existing:
            existing.open_price = open_price
            existing.close_price = close_price
            existing.min_price = min_price
            existing.max_price = max_price
            existing.volume = volume
            existing.is_complete = is_complete
        else:
            record = CandleDB(
                ticker=ticker,
                date=date,
                open_price=open_price,
                close_price=close_price,
                min_price=min_price,
                max_price=max_price,
                volume=volume,
                is_complete=is_complete
            )
            session.add(record)
        
        session.commit()


@logger.error_logger
def bulk_insert_candles(candles: list[dict]) -> None:
    with Session(engine) as session:
        for candle_data in candles:
            existing = session.query(CandleDB).filter(
                and_(
                    CandleDB.ticker == candle_data['ticker'],
                    CandleDB.date == candle_data['date']
                )
            ).first()
            
            if existing:
                existing.open_price = candle_data['open_price']
                existing.close_price = candle_data['close_price']
                existing.min_price = candle_data['min_price']
                existing.max_price = candle_data['max_price']
                existing.volume = candle_data['volume']
                existing.is_complete = candle_data.get('is_complete', True)
            else:
                record = CandleDB(
                    ticker=candle_data['ticker'],
                    date=candle_data['date'],
                    open_price=candle_data['open_price'],
                    close_price=candle_data['close_price'],
                    min_price=candle_data['min_price'],
                    max_price=candle_data['max_price'],
                    volume=candle_data['volume'],
                    is_complete=candle_data.get('is_complete', True)
                )
                session.add(record)
        
        session.commit()


@logger.error_logger
def get_missing_date_ranges(
    ticker: str,
    date_from: datetime.datetime,
    date_to: datetime.datetime,
    existing_candles: Optional[list[CandleDB]] = None
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """
    Find missing date ranges in candle data.
    
    Args:
        ticker: Instrument ticker
        date_from: Start date
        date_to: End date
        existing_candles: Optional list of existing candles to reuse (avoids duplicate DB query)
    
    Returns:
        List of (start, end) tuples representing missing date ranges
    
    Time complexity: O(n log n) where n = number of existing candles
    """
    if date_from.tzinfo is not None:
        date_from = date_from.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    if date_to.tzinfo is not None:
        date_to = date_to.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    
    if existing_candles is None:
        with Session(engine) as session:
            existing_candles = session.query(CandleDB).filter(
                and_(
                    CandleDB.ticker == ticker,
                    CandleDB.date >= date_from,
                    CandleDB.date <= date_to,
                    CandleDB.is_complete == True
                )
            ).order_by(CandleDB.date).all()
    
    if not existing_candles:
        return [(date_from, date_to)]
    
    existing_dates_sorted = sorted([
        c.date.date() if isinstance(c.date, datetime.datetime) else c.date 
        for c in existing_candles
    ])
    
    missing_ranges = []
    date_from_date = date_from.date() if isinstance(date_from, datetime.datetime) else date_from
    date_to_date = date_to.date() if isinstance(date_to, datetime.datetime) else date_to
    
    if existing_dates_sorted[0] > date_from_date:
        missing_ranges.append((
            date_from,
            datetime.datetime.combine(existing_dates_sorted[0] - datetime.timedelta(days=1), datetime.time.max)
        ))
    
    for i in range(len(existing_dates_sorted) - 1):
        current = existing_dates_sorted[i]
        next_date = existing_dates_sorted[i + 1]
        gap_days = (next_date - current).days
        
        if gap_days > 1:
            missing_ranges.append((
                datetime.datetime.combine(current + datetime.timedelta(days=1), datetime.time.min),
                datetime.datetime.combine(next_date - datetime.timedelta(days=1), datetime.time.max)
            ))
    
    if existing_dates_sorted[-1] < date_to_date:
        missing_ranges.append((
            datetime.datetime.combine(existing_dates_sorted[-1] + datetime.timedelta(days=1), datetime.time.min),
            date_to
        ))
    
    return missing_ranges
