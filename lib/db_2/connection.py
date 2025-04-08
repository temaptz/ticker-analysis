import sqlalchemy
import time
import const
from lib import docker

def get_engine(retries=50, delay=1):
    db_host = get_db_host()
    db_url = f'postgresql+psycopg2://{const.DB_USERNAME}:{const.DB_PASSWORD}@{db_host}:5432/{const.DB_NAME}'

    for attempt in range(1, retries + 1):
        try:
            engine = sqlalchemy.create_engine(db_url)
            with engine.connect():
                return engine
        except sqlalchemy.exc.OperationalError as e:
            print(f'⏳ [{attempt}/{retries}] БД не готова, жду {delay}с... ({e})')
            time.sleep(delay)

    raise RuntimeError(f'Не удалось подключиться к БД после {retries} попыток')


def get_db_host() -> str:
    return const.DB_HOST if docker.is_docker() else 'localhost'
