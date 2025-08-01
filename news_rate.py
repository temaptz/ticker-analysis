import time
from dotenv import load_dotenv
from lib import docker, logger, agent

load_dotenv()


print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_docker():
    while True:
        start = time.time()
        logger.log_info(f'START RATE ALL NEWS')
        agent.news_rank.rank_last_news()
        end = time.time()
        logger.log_info(f'RATE ALL NEWS FINISHED IN TIME: {end - start} sec.')
        time.sleep(60)
