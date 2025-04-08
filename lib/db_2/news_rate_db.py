import datetime
import uuid
import sqlalchemy
from typing import Optional
from sqlalchemy import Column, DateTime, Text, String, select, UUID
from sqlalchemy.orm import declarative_base, Session
from lib import yandex, serializer
from lib.db_2 import connection

Base = declarative_base()
engine = connection.get_engine()


class NewsRateCache(Base):
    __tablename__ = 'news_rate_cache'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_uid = Column(String)
    instrument_uid = Column(String)
    rate = Column(Text)  # JSON as string
    date = Column(DateTime, default=datetime.datetime.now(datetime.UTC))

def init_table():
    Base.metadata.create_all(engine)


def get_rate_by_uid(news_uid: str, instrument_uid: str) -> Optional[yandex.NewsRate]:
    with Session(engine) as session:
        row = session.execute(
            select(NewsRateCache)
            .where(NewsRateCache.news_uid == news_uid)
            .where(NewsRateCache.instrument_uid == instrument_uid)
        ).scalar_one_or_none()

        if row and row.rate:
            deserialized_dict = serializer.from_json(row.rate)
            return yandex.NewsRate(
                positive_percent=deserialized_dict.get('positive_percent', 0),
                negative_percent=deserialized_dict.get('negative_percent', 0),
                neutral_percent=deserialized_dict.get('neutral_percent', 0),
            )
        return None


def insert_rate(news_uid: str, instrument_uid: str, rate: yandex.NewsRate, date=datetime.datetime.now(datetime.UTC)):
    rate_json = serializer.to_json(rate)
    if rate_json:
        with Session(engine) as session:
            stmt = sqlalchemy.insert(NewsRateCache).values(
                news_uid=news_uid,
                instrument_uid=instrument_uid,
                rate=rate_json,
                date=date,
            )

            session.execute(stmt)
            session.commit()
