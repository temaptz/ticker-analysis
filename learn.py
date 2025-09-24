from lib import docker, telegram, cache
from lib.learn import ta_1_2, ta_2, ta_2_1, consensus

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_prod():
    cache.clean()

    telegram.send_message('[LEARN] Начало обучения TA-2_1')
    ta_2_1.generate_data()
    ta_2_1.learn()
    telegram.send_message('[LEARN] Обучение TA-2_1 завершено')

    cache.clean()

    # telegram.send_message('[LEARN] Начало обучения TA-2')
    # ta_2.generate_data()
    # ta_2.learn()
    # telegram.send_message('[LEARN] Обучение TA-2 завершено')
    #
    # cache.clean()
    #
    # telegram.send_message('[LEARN] Начало обучения TA-1_2')
    # ta_1_2.generate_data()
    # ta_1_2.learn()
    # telegram.send_message('[LEARN] Обучение TA-1_2 завершено')
    #
    # cache.clean()

    # telegram.send_message('[LEARN] Начало обучения TA-consensus')
    # consensus.learn()
    # telegram.send_message('[LEARN] Обучение TA-consensus завершено')
    #
    # cache.clean()
