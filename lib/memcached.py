import os
import memcache
from lib import docker

# Получаем хост и порт Memcached из переменных окружения
MEMCACHED_HOST = os.getenv('MEMCACHED_HOST', 'memcached' if docker.is_docker() else 'localhost')
MEMCACHED_PORT = os.getenv('MEMCACHED_PORT', '11211')

# Подключение к Memcached
mc = memcache.Client([f'{MEMCACHED_HOST}:{MEMCACHED_PORT}'], debug=0)


# Функции работы с кэшем
def cache_set(key, value, ttl_sec=600):
    """Записывает значение в кэш на 10 минут (600 секунд)"""
    mc.set(key, value, ttl_sec)


def cache_get(key):
    """Получает значение из кэша"""
    return mc.get(key)


def cache_delete(key):
    """Удаляет значение из кэша"""
    mc.delete(key)


def cache_clean():
    return mc.flush_all()


def get_memcached_stats():
    """Возвращает статистику Memcached"""
    memcached_stats = {}
    stats = mc.get_stats()
    if stats:
        memcached_stats = stats[0][1]

    return f'''
        Статистика Memcached: {memcached_stats}\n
        Размер занятого кэша: {get_memcached_size_mb()} MB\n
        Всего сохранено объектов: {memcached_stats.get('curr_items', 0)}\n
        Максимальный объем кэша: {get_memcached_max_size_mb()} MB\n
    '''


def get_memcached_max_size_mb() -> float:
    """Возвращает статистику Memcached"""
    try:
        memcached_stats = {}
        stats = mc.get_stats()
        if stats:
            memcached_stats = stats[0][1]

        return round(int(memcached_stats.get('limit_maxbytes', 0)) / 1024 / 1024, 2)

    except Exception as e:
        print('ERROR get_memcached_max_size_mb', e)
        return 0


def get_memcached_size_mb() -> float:
    """Возвращает статистику Memcached"""
    try:
        memcached_stats = {}
        stats = mc.get_stats()
        if stats:
            memcached_stats = stats[0][1]

        return round(int(memcached_stats.get('bytes', 0)) / 1024 / 1024, 2)

    except Exception as e:
        print('ERROR get_memcached_size_mb', e)
        return 0
