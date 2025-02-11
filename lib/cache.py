import time
from cachetools import LRUCache, TTLCache
from functools import wraps

cache = LRUCache(maxsize=100)
expirations = {}


def get(key: str):
    if key in cache and time.time() < expirations.get(key, 0):
        return cache[key]
    cache.pop(key, None)  # Удаляем устаревший ключ
    expirations.pop(key, None)
    return None


def set(key: str, value: any, ttl: int = 3600) -> None:
    cache[key] = value
    expirations[key] = time.time() + ttl


def ttl_cache(ttl: int = 3600, maxsize: int = 1024):
    """Декоратор кэширования с временем жизни (ttl) и ограничением по размеру."""
    c = TTLCache(maxsize=maxsize, ttl=ttl)  # Создаём кэш

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                key = (args, frozenset(kwargs.items()))  # Создаём ключ на основе аргументов
                if key in c:
                    return c[key]  # Возвращаем из кэша, если есть
                result = func(*args, **kwargs)  # Вычисляем функцию
                c[key] = result  # Сохраняем в кэше
                return result

            except Exception as e:
                print('ERROR ttl_cache decorator', e)

        return wrapper
    return decorator
