import datetime
from typing import Optional
from sqlalchemy import Column, DateTime, String, select
from sqlalchemy.orm import declarative_base, Session
from lib.db_2.connection import get_engine
from lib import logger

Base = declarative_base()
engine = get_engine()


class GptRequest(Base):
    __tablename__ = 'gpt_requests'

    request = Column(String, primary_key=True)
    response = Column(String, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_response(request: str) -> Optional[str]:
    with Session(engine) as session:
        row = session.execute(
            select(GptRequest.response).where(GptRequest.request == request)
        ).scalar_one_or_none()
        return row


@logger.error_logger
def insert_response(request: str, response: str, date=datetime.datetime.now(datetime.UTC)) -> None:
    with Session(engine) as session:
        record = GptRequest(request=request, response=response, date=date)
        session.add(record)
        session.commit()
