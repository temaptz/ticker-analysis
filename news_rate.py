import os
import time
from dotenv import load_dotenv
from lib import docker

load_dotenv()

if os.getenv('OLLAMA_MODEL_NAME'):
    os.environ['OLLAMA_MODEL_NAME'] = os.getenv('OLLAMA_MODEL_NAME')

from lib import agent


print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_docker():
    while True:
        agent.news_rank.rank_last_news()
        time.sleep(3600)
