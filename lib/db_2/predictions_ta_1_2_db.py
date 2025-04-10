import datetime
import uuid
from typing import Type
from sqlalchemy import Column, DateTime, Float, String, and_, UUID
from sqlalchemy.orm import declarative_base, Session
from lib.db_2.connection import get_engine
from lib import logger

Base = declarative_base()
engine = get_engine()


class PredictionTa11(Base):
    __tablename__ = 'predictions_ta_1_2'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_uid = Column(String, nullable=False)
    prediction = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.datetime.now(datetime.timezone.utc))
    target_date = Column(DateTime, nullable=False, default=datetime.datetime)


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_predictions() -> list[Type[PredictionTa11]]:
    with Session(engine) as session:
        return session.query(PredictionTa11).all()


@logger.error_logger
def get_predictions_by_uid_date(uid: str, date_from: datetime.datetime, date_to: datetime.datetime) -> list[
    Type[PredictionTa11]]:
    with Session(engine) as session:
        return session.query(PredictionTa11).filter(
            and_(
                PredictionTa11.instrument_uid == uid,
                PredictionTa11.date.between(date_from, date_to)
            )
        ).all()


@logger.error_logger
def insert_prediction(uid: str, prediction: float, target_date: datetime.datetime, date=datetime.datetime.now(datetime.UTC)) -> None:
    with Session(engine) as session:
        record = PredictionTa11(instrument_uid=uid, prediction=prediction, date=date, target_date=target_date)
        session.add(record)
        session.commit()
