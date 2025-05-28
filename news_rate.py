import time
from lib import docker, news, logger


print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_docker():
    while True:
        start = time.time()
        logger.log_info(f'START RATE ALL NEWS')
        news.rate_background.rate_all_news()
        end = time.time()
        logger.log_info(f'RATE ALL NEWS FINISHED IN TIME: {end - start} sec.')
        time.sleep(3600)
