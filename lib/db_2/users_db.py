import datetime
import uuid
import sqlalchemy
from sqlalchemy import Column, DateTime, String, UUID
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import declarative_base, Session
from lib.db_2.connection import get_engine
from lib import logger
from werkzeug.security import generate_password_hash, check_password_hash

Base = declarative_base()
engine = get_engine()


class UserDB(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    login = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    date_create = Column(DateTime, nullable=False, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    token = Column(String, nullable=True)
    t_invest_token = Column(String, nullable=True)
    ticker_list = Column(String, nullable=True)

    def set_password_hash(self, password: str) -> None:
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password)


@logger.error_logger
def init_table() -> None:
    Base.metadata.create_all(engine)


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return check_password_hash(hashed_password, password)


def get_user_by_id(user_id: str) -> UserDB or None:
    with Session(engine) as session:
        return session.query(UserDB).filter(
            UserDB.id == user_id,
        ).one()


def get_user_by_login(login: str) -> UserDB or None:
    with Session(engine) as session:
        return session.query(UserDB).filter(
            UserDB.login == login,
        ).one_or_none()


def get_user_by_token(token: str) -> UserDB or None:
    with Session(engine) as session:
        return session.query(UserDB).filter(
            UserDB.token == token,
        ).one_or_none()


def update_user_token(user_id: str, token: str):
    with Session(engine) as session:
        if user := session.query(UserDB).filter(
            UserDB.id == user_id,
            ).one_or_none():

            user.token = token

            session.commit()
