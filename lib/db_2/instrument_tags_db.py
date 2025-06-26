import datetime
import uuid
from typing import Optional, Sequence
from sqlalchemy import String, UUID, UniqueConstraint, func, text, select
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert, TIMESTAMP
from lib.db_2.connection import get_engine
from lib import logger


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase): ...

class TagDB(Base):
    __tablename__ = 'instrument_tags'
    __table_args__ = (
        UniqueConstraint('instrument_uid', 'tag_name', name='instrument_tag_uq'),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text('gen_random_uuid()'),
    )
    instrument_uid: Mapped[str] = mapped_column(String(64), nullable=False)
    tag_name:       Mapped[str] = mapped_column(String(64), nullable=False)
    tag_value:      Mapped[str] = mapped_column(String(256), nullable=False)
    date:           Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_tags() -> Sequence[TagDB]:
    stmt = select(TagDB)
    with SessionLocal() as session:
        return list(session.scalars(stmt))


@logger.error_logger
def get_tag(instrument_uid: str, tag_name: str) -> Optional[TagDB]:
    stmt = (
        select(TagDB)
        .where(
            TagDB.instrument_uid == instrument_uid,
            TagDB.tag_name == tag_name,
            )
    )
    with SessionLocal() as session:
        return session.scalar(stmt)


@logger.error_logger
def upsert_tag(instrument_uid: str, tag_name: str, tag_value: str) -> None:
    stmt = (
        pg_insert(TagDB)
        .values(
            instrument_uid=instrument_uid,
            tag_name=tag_name,
            tag_value=tag_value,
        )
        .on_conflict_do_update(
            constraint='instrument_tag_uq',
            set_={
                'tag_value': tag_value,
                'date': func.now(),
            },
        )
    )

    with SessionLocal() as session, session.begin():
        session.execute(stmt)
