import sqlalchemy
import time
import const
from lib import docker


def get_db_host() -> str:
    return const.DB_HOST if docker.is_docker() else 'localhost'


def _get_engine(retries=50, delay=1):
    db_host = get_db_host()
    db_url = f'postgresql+psycopg2://{const.DB_USERNAME}:{const.DB_PASSWORD}@{db_host}:5432/{const.DB_NAME}'

    for attempt in range(1, retries + 1):
        try:
            engine = sqlalchemy.create_engine(
                db_url,
                pool_pre_ping=True,
                pool_recycle=280,
                pool_size=2,
                max_overflow=5,
                pool_timeout=30,
            )
            with engine.connect():
                return engine
        except sqlalchemy.exc.OperationalError as e:
            print(f'⏳ [{attempt}/{retries}] БД не готова, жду {delay}с... ({e})')
            time.sleep(delay)

    raise RuntimeError(f'Не удалось подключиться к БД после {retries} попыток')


_engine = _get_engine()


def get_engine():
    return _engine
