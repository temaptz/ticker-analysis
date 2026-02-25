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
    date_to: datetime.datetime
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    with Session(engine) as session:
        if date_from.tzinfo is not None:
            date_from = date_from.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        if date_to.tzinfo is not None:
            date_to = date_to.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        
        existing_dates = session.query(CandleDB.date).filter(
            and_(
                CandleDB.ticker == ticker,
                CandleDB.date >= date_from,
                CandleDB.date <= date_to,
                CandleDB.is_complete == True
            )
        ).order_by(CandleDB.date).all()
        
        existing_dates_set = {d[0].date() if isinstance(d[0], datetime.datetime) else d[0] for d in existing_dates}
        
        missing_ranges = []
        current_date = date_from.date() if isinstance(date_from, datetime.datetime) else date_from
        end_date = date_to.date() if isinstance(date_to, datetime.datetime) else date_to
        range_start = None
        
        while current_date <= end_date:
            if current_date not in existing_dates_set:
                if range_start is None:
                    range_start = current_date
            else:
                if range_start is not None:
                    missing_ranges.append((
                        datetime.datetime.combine(range_start, datetime.time.min),
                        datetime.datetime.combine(current_date - datetime.timedelta(days=1), datetime.time.max)
                    ))
                    range_start = None
            
            current_date += datetime.timedelta(days=1)
        
        if range_start is not None:
            missing_ranges.append((
                datetime.datetime.combine(range_start, datetime.time.min),
                datetime.datetime.combine(end_date, datetime.time.max)
            ))
        
        return missing_ranges
