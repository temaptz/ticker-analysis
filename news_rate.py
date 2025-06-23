import time
from lib import docker, news, logger, instruments


print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_docker():
    while True:
        max_iterations_count = (len(instruments.get_instruments_white_list()) * 30) or 10000
        start = time.time()
        logger.log_info(f'START RATE ALL NEWS')
        news.rate_background.run_rate_cycle(max_iterations_count=max_iterations_count)
        end = time.time()
        logger.log_info(f'RATE ALL NEWS FINISHED IN TIME: {end - start} sec.')
        time.sleep(3600)
