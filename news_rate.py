from lib import docker, news


print('IS DOCKER', docker.is_docker())
print('IS PROD', docker.is_prod())

if docker.is_docker():
    news.rate_background.rate_all_news()
