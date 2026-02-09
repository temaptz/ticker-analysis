from lib import docker, telegram
from lib.learn import ta_3_technical_learn, model

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_prod():
    telegram.send_message(f'[LEARN] Начало обучения {model.TA_3_tech}')
    ta_3_technical_learn.generate_data()
    telegram.send_message(f'[LEARN] Обучение {model.TA_3_tech} завершено')
