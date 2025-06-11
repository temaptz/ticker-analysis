import datetime
import uuid
from typing import Type
from sqlalchemy import Column, DateTime, Float, String, and_, UUID
from sqlalchemy.orm import declarative_base, Session
from lib.db_2.connection import get_engine
from lib import logger, date_utils

Base = declarative_base()
engine = get_engine()


class PredictionDB(Base):
    __tablename__ = 'predictions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_uid = Column(String, nullable=False)
    prediction = Column(Float, nullable=False)
    target_date = Column(DateTime, nullable=False, default=datetime.datetime)
    model_name = Column(String, nullable=False)
    date = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_predictions() -> list[Type[PredictionDB]]:
    with Session(engine) as session:
        return session.query(PredictionDB).all()


@logger.error_logger
def get_predictions_by_uid_date(
        uid: str,
        date_from: datetime.datetime,
        date_to: datetime.datetime,
        model_name: str = None
) -> list[PredictionDB]:
    with (Session(engine) as session):
        query = session.query(PredictionDB).filter(
            and_(
                PredictionDB.instrument_uid == uid,
                PredictionDB.target_date.between(date_from, date_to),
                PredictionDB.model_name == model_name,
            )
        )

        res = query.all()

        return res


@logger.error_logger
def get_unique_dates() -> set[datetime.datetime]:
    with Session(engine) as session:
        return {date_utils.parse_date(date) for date, in session.query(PredictionDB.date).distinct()}


@logger.error_logger
def insert_prediction(
        instrument_uid: str,
        prediction: float,
        target_date: datetime.datetime,
        model_name: str,
        date=datetime.datetime.now(datetime.timezone.utc)
) -> None:
    with Session(engine) as session:
        record = PredictionDB(
            instrument_uid=instrument_uid,
            prediction=float(prediction),
            target_date=target_date,
            model_name=model_name,
            date=date,
        )
        session.add(record)
        session.commit()
