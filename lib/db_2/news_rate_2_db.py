import datetime
import uuid

import sqlalchemy
from sqlalchemy.orm import declarative_base, Session
from tinkoff.invest import StatisticResponse

from lib.db_2.connection import get_engine
from lib import logger, serializer, types_util

Base = declarative_base()
engine = get_engine()


class NewsRate2Db(Base):
    __tablename__ = 'news_rate_2'

    id = sqlalchemy.Column(sqlalchemy.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_uid = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    instrument_uid = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    sentiment = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    impact_strength = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    mention_focus = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    model_name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    pretrain_name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    generation_time_sec = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    generation_date = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_rate(instrument_uid: str, news_uid: str) -> list[NewsRate2Db]:
    with Session(engine) as session:
        return session.query(NewsRate2Db).filter(
            NewsRate2Db.instrument_uid == instrument_uid,
            NewsRate2Db.news_uid == news_uid
        ).order_by(
            NewsRate2Db.generation_date.desc()
        ).all()


@logger.error_logger
def insert_or_update_rate(
        news_uid: str,
        instrument_uid: str,
        news_rate: types_util.NewsRate2,
        model_name: str,
        generation_time_sec: float,
        pretrain_name: str = None,
) -> None:
    with Session(engine) as session:
        record = NewsRate2Db(
            news_uid=news_uid,
            instrument_uid=instrument_uid,
            sentiment=news_rate.sentiment,
            impact_strength=news_rate.impact_strength,
            mention_focus=news_rate.mention_focus,
            model_name=model_name,
            pretrain_name=pretrain_name,
            generation_time_sec=generation_time_sec,
            generation_date=datetime.datetime.now(datetime.timezone.utc),
        )

        rate_existing = session.query(NewsRate2Db).filter(
            NewsRate2Db.instrument_uid == instrument_uid,
            NewsRate2Db.news_uid == news_uid,
            NewsRate2Db.model_name == model_name,
            NewsRate2Db.pretrain_name == pretrain_name,
        ).one_or_none()

        if rate_existing:
            rate_existing.sentiment = record.sentiment
            rate_existing.impact_strength = record.impact_strength
            rate_existing.mention_focus = record.mention_focus
            rate_existing.model_name = record.model_name
            rate_existing.pretrain_name = record.pretrain_name
            rate_existing.generation_time_sec = record.generation_time_sec
            rate_existing.generation_date = record.generation_date

        else:
            session.add(record)

        session.commit()
