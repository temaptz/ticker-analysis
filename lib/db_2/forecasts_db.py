import datetime
import uuid
import sqlalchemy
from typing import Type
from sqlalchemy import Column, DateTime, LargeBinary, String, func, UUID
from sqlalchemy.orm import declarative_base, Session
from t_tech.invest.schemas import GetForecastResponse

from lib.db_2.connection import get_engine  # должен возвращать SQLAlchemy engine
from lib import logger, serializer

Base = declarative_base()
engine = get_engine()


class Forecast(Base):
    __tablename__ = 'forecasts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_uid = Column(String)
    forecasts = Column(LargeBinary, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_forecasts() -> list[Type[Forecast]]:
    with Session(engine) as session:
        return session.query(Forecast).all()


@logger.error_logger
def get_forecasts_by_uid(uid: str) -> list[Type[Forecast]]:
    with Session(engine) as session:
        return session.query(Forecast).filter(Forecast.instrument_uid == uid).all()


@logger.error_logger
def get_forecasts_by_uid_date(
        instrument_uid: str,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
) -> list[Type[Forecast]]:
    with (Session(engine) as session):
        return session.query(Forecast).filter(
            sqlalchemy.and_(
                Forecast.instrument_uid == instrument_uid,
                Forecast.date.between(start_date, end_date)
            )
        ).all()


@logger.error_logger
def get_forecast_by_uid_date(uid: str, date: datetime.datetime) -> Type[Forecast] or None:
    with (Session(engine) as session):
        # Находим ближайшую по времени запись
        results = session.query(Forecast).filter(Forecast.instrument_uid == uid).order_by(
            func.abs(func.extract('epoch', Forecast.date) - func.extract('epoch', date))
        ).limit(1).all()

        if results and results[0]:
            return results[0]

    return None


@logger.error_logger
def insert_forecast(instrument_uid: str, forecast: GetForecastResponse, date=datetime.datetime.now(datetime.UTC)) -> None:
    binary_data = serializer.db_serialize(forecast)

    with Session(engine) as session:
        record = Forecast(instrument_uid=instrument_uid, forecasts=binary_data, date=date)
        session.add(record)
        session.commit()
