import datetime
import uuid
from typing import Type
from sqlalchemy import Column, DateTime, LargeBinary, String, func, UUID
from sqlalchemy.orm import declarative_base, Session
from tinkoff.invest import StatisticResponse

from lib.db_2.connection import get_engine
from lib import logger, serializer

Base = declarative_base()
engine = get_engine()


class Fundamental(Base):
    __tablename__ = 'fundamentals'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_uid = Column(String)
    fundamentals = Column(LargeBinary, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_fundamentals() -> list[Fundamental]:
    with Session(engine) as session:
        return session.query(Fundamental).all()


@logger.error_logger
def get_fundamentals_by_asset_uid(asset_uid: str) -> list[Fundamental]:
    with Session(engine) as session:
        return session.query(Fundamental).filter(Fundamental.asset_uid == asset_uid).all()


@logger.error_logger
def get_fundamentals_by_asset_uid_date(asset_uid: str, date: datetime.datetime) -> Fundamental or None:
    with Session(engine) as session:
        results = session.query(Fundamental).filter(Fundamental.asset_uid == asset_uid).order_by(
            func.abs(func.extract('epoch', Fundamental.date) - func.extract('epoch', date))
        ).limit(1).all()

        if results and results[0]:
            return results[0]
        return None


@logger.error_logger
def insert_fundamentals(asset_uid: str, fundamental: StatisticResponse, date=datetime.datetime.now(datetime.UTC)) -> None:
    with Session(engine) as session:
        record = Fundamental(
            asset_uid=asset_uid,
            fundamentals=serializer.db_serialize(fundamental),
            date=date
        )
        session.add(record)
        session.commit()
