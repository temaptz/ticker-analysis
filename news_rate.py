import os
import time
from dotenv import load_dotenv
from lib import docker, logger

load_dotenv()

# Гарантируем, что переменная окружения модели LLM установлена из .env
if os.getenv('OLLAMA_MODEL_NAME'):
    os.environ['OLLAMA_MODEL_NAME'] = os.getenv('OLLAMA_MODEL_NAME')

from lib import agent


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
