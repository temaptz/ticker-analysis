import datetime
import uuid
import sqlalchemy
from sqlalchemy import Column, DateTime, Text, String, select, UUID
from sqlalchemy.orm import declarative_base, Session
from yandex_cloud_ml_sdk._models.text_classifiers.model import FewShotTextClassifiersModelResult
from lib import serializer, utils
from lib.db_2 import connection

Base = declarative_base()
engine = connection.get_engine()


class NewsClassifyGptCache(Base):
    __tablename__ = 'news_classify_gpt_cache'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    news_hash = Column(String)
    subject_name = Column(String)
    classify = Column(Text)  # JSON as string
    date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

def init_table():
    Base.metadata.create_all(engine)


def get_classify(news_hash: str, subject_name: str) -> NewsClassifyGptCache or None:
    with Session(engine) as session:
        resp = session.execute(
            select(NewsClassifyGptCache)
            .where(NewsClassifyGptCache.news_hash == news_hash)
            .where(NewsClassifyGptCache.subject_name == subject_name)
            .order_by(sqlalchemy.desc(NewsClassifyGptCache.date))
            .limit(1)
        ).all()

        if resp and len(resp) > 0 and resp[0] and resp[0][0]:
            return resp[0][0]

        return None


def insert_classify(news_hash: str, subject_name: str, classify: FewShotTextClassifiersModelResult, date=datetime.datetime.now(datetime.UTC)):
    classify_json = serializer.to_json(classify)
    if classify_json:
        with Session(engine) as session:
            stmt = sqlalchemy.insert(NewsClassifyGptCache).values(
                news_hash=news_hash,
                subject_name=subject_name,
                classify=classify_json,
                date=date,
            )

            session.execute(stmt)
            session.commit()


def get_model_result_by_record(record: NewsClassifyGptCache) -> FewShotTextClassifiersModelResult or None:
    try:
        if record and record.classify and len(str(record.classify)) > 0:
            decoded: FewShotTextClassifiersModelResult = serializer.from_json(record.classify)
            if decoded and 'predictions' in decoded:
                return decoded
    except Exception as e:
        print('ERROR get_model_result_by_record', e)

    return None


def get_news_hash(news_title: str, news_text: str) -> str:
    return utils.get_md5(serializer.to_json({
        'news_title': news_title,
        'news_text': news_text,
    }))
