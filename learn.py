from lib import docker, telegram
from lib.learn import ta_3_fundamental_learn, model, ta_3_volume_learn

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_prod():
    telegram.send_message(f'[LEARN] Начало обучения {model.TA_3_fundamental}')
    ta_3_fundamental_learn.generate_data()
    telegram.send_message(f'[LEARN] Обучение {model.TA_3_fundamental} завершено')

    telegram.send_message(f'[LEARN] Начало обучения {model.TA_3_volume}')
    ta_3_volume_learn.generate_data()
    telegram.send_message(f'[LEARN] Обучение {model.TA_3_volume} завершено')
