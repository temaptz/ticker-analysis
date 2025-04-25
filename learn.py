from lib import (
    docker,
)
from lib.learn import ta_2

print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_prod():
    ta_2.generate_data()
    # ta_2.learn()
