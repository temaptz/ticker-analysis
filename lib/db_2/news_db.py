import sqlalchemy
from sqlalchemy import Column, MetaData, DateTime, Text, func, and_, insert, desc
from sqlalchemy.dialects.postgresql import UUID, TSVECTOR
from sqlalchemy.sql import text as sql_text
from sqlalchemy.orm import Session, declarative_base
import datetime
from typing import Type, Any

from lib.db_2 import connection
from lib import logger, serializer

engine = connection.get_engine()
metadata = MetaData()
Base = declarative_base(metadata=metadata)

table_name = 'news'

class News(Base):
    __tablename__ = table_name

    news_uid = Column(sqlalchemy.String, primary_key=True)
    date = Column(DateTime, nullable=False)
    source_name = Column(Text)
    title = Column(Text)
    text = Column(Text)
    search_vector = Column(TSVECTOR, nullable=True)


@logger.error_logger
def init_tables() -> None:
    with engine.begin() as conn:
        conn.execute(sql_text('CREATE EXTENSION IF NOT EXISTS unaccent;'))
        Base.metadata.create_all(engine)
        conn.execute(sql_text(f'''
            CREATE INDEX IF NOT EXISTS {table_name}_search_idx
            ON {table_name}
            USING GIN (search_vector);
        '''))


@logger.error_logger
def get_news() -> list[Type[News]]:
    with Session(engine) as session:
        return session.query(News).all()


@logger.error_logger
def get_news_by_uid(news_uid: str) -> Type[News]:
    with Session(engine) as session:
        return session.query(News).filter(News.news_uid == news_uid).one_or_none()


@logger.error_logger
def get_news_by_date_keywords_fts(
        start_date: datetime.datetime,
        end_date: datetime.datetime,
        keywords: list[str],
) -> list[News]:
    if not keywords:
        return []

    query_string = build_ts_query(keywords)
    safe_query_string = query_string.replace("'", "''")

    raw_sql = f"""
        SELECT news_uid, date, source_name, title, text, search_vector
        FROM news
        WHERE date BETWEEN :start_date AND :end_date
          AND search_vector @@ to_tsquery('russian', unaccent('{safe_query_string}'))
        ORDER BY date DESC
    """

    with Session(engine) as session:
        result = session.execute(
            sqlalchemy.text(raw_sql),
            {"start_date": start_date, "end_date": end_date}
        ).mappings()

        rows = result.fetchall()

        result = [News(
            news_uid=row['news_uid'],
            date=row['date'],
            source_name=row['source_name'],
            title=row['title'],
            text=row['text'],
        ) for row in rows]

        return result


@logger.error_logger
def insert_news(record: News) -> None:
    with (Session(engine) as session):
        search_vector_expr = (
            func.setweight(func.to_tsvector('russian', func.unaccent(record.title)), 'A')
            .op('||')(
                func.setweight(func.to_tsvector('russian', func.unaccent(record.text)), 'B')
            )
        )

        stmt = sqlalchemy.dialects.postgresql.insert(News).values(
            news_uid=record.news_uid,
            date=record.date,
            source_name=record.source_name,
            title=record.title,
            text=record.text,
            search_vector=search_vector_expr
        ).on_conflict_do_nothing(
            index_elements=['news_uid']
        )
        session.execute(stmt)
        session.commit()


def build_ts_query(keywords: list[str]) -> str:
    """
    Формирует ts_query для PostgreSQL с учётом фраз (ключевых слов с пробелами).
    Между словами внутри фразы ставит оператор <-> (точная последовательность слов).
    Между отдельными ключевыми словами ставит оператор | (ИЛИ).
    """
    terms = []
    for kw in keywords:
        words = kw.strip().split()
        if len(words) > 1:
            phrase = ' <-> '.join(words)
            terms.append(f'({phrase})')
        else:
            terms.append(words[0])
    return ' | '.join(terms)