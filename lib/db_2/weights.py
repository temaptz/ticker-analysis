import datetime
import uuid
from typing import Optional, Sequence
import sqlalchemy
from sqlalchemy import String, UUID, UniqueConstraint, func, text, select, Integer, Float
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase, sessionmaker
from sqlalchemy.dialects.postgresql import TIMESTAMP
from lib.db_2.connection import get_engine
from lib import logger


engine = get_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

class Base(DeclarativeBase): ...

class WeightDB(Base):
    __tablename__ = 'weights'
    __table_args__ = (
        UniqueConstraint('name', name='weight_name_uq'),
    )

    id:  Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:  Mapped[str] = mapped_column(String(64), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    date:  Mapped[datetime.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


@logger.error_logger
def get_all_weights() -> Sequence[WeightDB]:
    stmt = select(WeightDB)
    with SessionLocal() as session:
        return list(session.scalars(stmt))


@logger.error_logger
def get_weight(name: str) -> Optional[WeightDB]:
    stmt = (
        select(WeightDB)
        .where(WeightDB.name == name)
    )
    with SessionLocal() as session:
        return session.scalar(stmt)


@logger.error_logger
def upset_weight(name: str, value: float) -> None:
    with SessionLocal() as session:
        existing = session.scalar(
            select(WeightDB).where(WeightDB.name == name)
        )

        if existing:
            existing.value = value
            existing.date = datetime.datetime.now(datetime.timezone.utc)
        else:
            session.add(WeightDB(name=name, value=value))

        session.commit()
