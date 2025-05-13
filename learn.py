from lib import docker, telegram
from lib.learn import ta_1_2,ta_2

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_prod():
    telegram.send_message('[LEARN] Начало обучения TA-1_2')
    ta_1_2.prepare_data()
    ta_1_2.learn()
    telegram.send_message('[LEARN] Обучение TA-1_2 завершено')

    telegram.send_message('[LEARN] Начало обучения TA-2')
    ta_2.generate_data()
    ta_2.learn()
    telegram.send_message('[LEARN] Обучение TA-2 завершено')
