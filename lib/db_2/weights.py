import datetime
import uuid
from typing import Optional, Sequence
import sqlalchemy
from sqlalchemy import String, UUID, UniqueConstraint, func, text, select, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert, TIMESTAMP
from lib.db_2.connection import get_engine
from lib import logger


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase): ...

class WeightDB(Base):
    __tablename__ = 'weights'

    id:  Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:  Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(sqlalchemy.Text, nullable=False)
    date:  Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_weight(name: str) -> Optional[WeightDB]:
    stmt = (
        select(WeightDB)
        .where(WeightDB.name == name)
    )
    with SessionLocal() as session:
        return session.get_one(stmt)


@logger.error_logger
def upset_weight(name: str, value: float) -> None:
    stmt = (
        pg_insert(WeightDB)
        .values(
            name=name,
            value=value,
        )
        .on_conflict_do_update()
    )

    with SessionLocal() as session, session.begin():
        session.execute(stmt)
