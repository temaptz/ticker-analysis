import subprocess
import const
from lib import logger, db_2, docker

@logger.error_logger
def backup_database(dump_file_path: str) -> None:
    pg_dump = 'pg_dump' if docker.is_docker() else '/usr/local/Cellar/postgresql@17/17.4_1/bin/pg_dump'

    subprocess.run([pg_dump, '--version'], check=True)

    cmd = [
        pg_dump,
        '-Fc',
        '-h', db_2.connection.get_db_host(),
        '-U', const.DB_USERNAME,
        const.DB_NAME  # имя базы — БЕЗ ключа -d
    ]
    # Открываем файл для записи дампа
    with open(dump_file_path, 'w') as f:
        # Запускаем pg_dump, перенаправляя вывод в файл
        subprocess.run(cmd, env={'PGPASSWORD': const.DB_PASSWORD}, stdout=f, check=True)


@logger.error_logger
def restore_database(dump_file_path: str):
    cmd = [
        'psql',
        '-h', db_2.connection.get_db_host(),
        '-U', const.DB_USERNAME,
        '-d', const.DB_NAME,
        '-f', dump_file_path
    ]
    subprocess.run(cmd, env={'PGPASSWORD': const.DB_PASSWORD}, check=True)
