import os
import redis
from lib import docker, serializer

REDIS_HOST = os.getenv('REDIS_HOST', 'redis' if docker.is_docker() else 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))

# Подключение к Redis
r_cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=False)
r_storage = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=1, decode_responses=False)


def cache_set(key: str, value: any, ttl_sec=600) -> None:
    """
    Записывает значение в Redis с TTL в секундах (по умолчанию 600 = 10 минут).
    """
    try:
        r_cache.set(name=key, value=serializer.db_serialize(data=value), ex=ttl_sec)
    except Exception as e:
        print('ERROR REDIS CACHE cache_set', e)


def cache_get(key: str) -> any:
    """
    Получает значение из Redis, или None, если ключа нет.
    """
    try:
        raw = r_cache.get(key)
        if raw:
            return serializer.db_deserialize(data=raw)
    except Exception as e:
        print('ERROR REDIS CACHE cache_get', e)

    return None


def storage_set(key: str, value: any, ttl_sec=600) -> None:
    """
    Записывает значение в Redis с TTL в секундах (по умолчанию 600 = 10 минут).
    """
    try:
        r_storage.set(name=key, value=serializer.db_serialize(data=value), ex=ttl_sec)
    except Exception as e:
        print('ERROR REDIS CACHE storage_set', e)


def storage_get(key: str) -> any:
    """
    Получает значение из Redis, или None, если ключа нет.
    """
    try:
        raw = r_storage.get(key)
        if raw:
            return serializer.db_deserialize(data=raw)
    except Exception as e:
        print('ERROR REDIS CACHE storage_get', e)

    return None


def storage_delete(key: str) -> None:
    """
    Удаляет ключ из Redis.
    """
    try:
        r_storage.delete(key)
    except Exception as e:
        print('ERROR REDIS CACHE storage_delete', e)


def clear_cache() -> None:
    """
    Полная очистка всех данных в текущей базе Redis.
    """
    try:
        r_cache.flushall()
    except Exception as e:
        print('ERROR REDIS CACHE cache_clean', e)


def get_redis_stats() -> str:
    """
    Возвращает строку со статистикой Redis, включая:
    - Основные метрики (r.info())
    - Занятая память
    - Кол-во ключей (db0: keys)
    - Макс. объём памяти (если настроено)
    """
    try:
        redis_info = r_cache.info()  # Словарь со множеством показателей
        used_memory_bytes = redis_info.get('used_memory', 0)
        used_memory_mb = round(used_memory_bytes / 1024 / 1024, 2)

        # Считаем текущие ключи в db0
        db0_info = redis_info.get('db0', {})
        total_keys = db0_info.get('keys', 0)

        # Запрашиваем maxmemory (если 0, значит не установлен)
        config_data = r_cache.config_get('maxmemory')
        max_memory_str = config_data.get('maxmemory', '0')
        max_memory = int(max_memory_str)
        max_memory_mb = round(max_memory / 1024 / 1024, 2) if max_memory > 0 else 0

        return f'''
        Статистика Redis:
          - used_memory: {used_memory_mb} MB
          - total_keys:  {total_keys}
          - max_memory:  {max_memory_mb if max_memory_mb > 0 else "не задан"} MB
        '''
    except Exception as e:
        print('ERROR CACHE get_redis_stats', e)
        return ''


def get_redis_max_size_mb() -> float:
    """
    Возвращает максимальный объём памяти (MB), настроенный для Redis.
    """
    try:
        config_data = r_cache.config_get('maxmemory')
        max_memory = int(config_data.get('maxmemory', '0'))
        return round(max_memory / 1024 / 1024, 2) if max_memory > 0 else 0.0
    except Exception as e:
        print('ERROR get_redis_max_size_mb:', e)
        return 0


def get_redis_size_mb() -> float:
    """
    Возвращает текущий объём занятой Redis памяти (MB).
    """
    try:
        redis_info = r_cache.info()
        used_memory_bytes = redis_info.get('used_memory', 0)
        return round(used_memory_bytes / 1024 / 1024, 2)
    except Exception as e:
        print('ERROR get_redis_size_mb:', e)
        return 0
