from lib import (
    telegram,
    docker,
    schedule,
    users,
    serializer,
    news,
    fundamentals_save
)
from lib.db import init
from lib.learn import ta_2

init.init_db()


if docker.is_docker():
    telegram.send_message('Скрипт ticker-analysis main запущен')
    schedule.start_schedule()
else:
    print('NOT DOCKER')
    ta_2.generate_data()
