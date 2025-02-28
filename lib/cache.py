import time
from cachetools import LRUCache
from functools import wraps
from lib import utils

cache = LRUCache(maxsize=100)
expirations = {}


def cache_get(key: str):
    if key in cache and time.time() < expirations.get(key, 0):
        return cache[key]
    cache.pop(key, None)  # Удаляем устаревший ключ
    expirations.pop(key, None)
    return None


def cache_set(key: str, value: any, ttl: int = 3600) -> None:
    cache[key] = value
    expirations[key] = time.time() + ttl


def ttl_cache(ttl: int = 3600, maxsize: int = 1024):
    """Декоратор кэширования с временем жизни (ttl) и ограничением по размеру."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                key_md5 = utils.get_md5(f'{func.__module__}.{func.__name__}:{args}:{kwargs}')
                saved_cache = cache_get(key=key_md5)
                if saved_cache:
                    return saved_cache  # Возвращаем из кэша, если есть

                result = func(*args, **kwargs)  # Вычисляем функцию
                cache_set(key=key_md5, value=result, ttl=ttl)  # Сохраняем в кэше

                return result

            except Exception as e:
                print('ERROR ttl_cache decorator', e)

        return wrapper
    return decorator
